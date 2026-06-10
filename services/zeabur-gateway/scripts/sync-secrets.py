#!/usr/bin/env python3
"""
把 .env 裡指定 bot 的 5 個 WeCom 密鑰推到 Zeabur service Variables。

用法：
    python services/zeabur-gateway/scripts/sync-secrets.py order-transform

冪等：執行多次只會更新值。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import request as _req
from urllib.error import HTTPError

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "services" / "zeabur-gateway"))

from lib import BotRegistry  # noqa: E402

API_URL = "https://api.zeabur.com/graphql"


def load_env():
    p = REPO_ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def gql(api_key: str, query: str, variables: dict | None = None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = _req.Request(API_URL, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "bikini-bottom-zeabur-sync/1.0",
    })
    try:
        with _req.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode('utf-8','replace')}")
    if data.get("errors"):
        raise SystemExit(json.dumps(data["errors"], ensure_ascii=False, indent=2))
    return data["data"]


def find_project(api_key: str, name: str):
    target = name.lower()
    data = gql(api_key, "{ projects { edges { node { _id name } } } }")
    for e in data["projects"]["edges"]:
        if e["node"]["name"].lower() == target:
            return e["node"]
    return None


def find_service(api_key: str, project_id: str, name: str):
    data = gql(
        api_key,
        """
        query S($p: ObjectID!) {
          services(projectID: $p) { edges { node { _id name } } }
        }
        """,
        {"p": project_id},
    )
    for e in data["services"]["edges"]:
        if e["node"]["name"] == name:
            return e["node"]
    return None


def get_environment_id(api_key: str, project_id: str) -> str:
    data = gql(
        api_key,
        "query($p: ObjectID!){ environments(projectID: $p){ _id name } }",
        {"p": project_id},
    )
    for e in data["environments"]:
        if e["name"] == "production":
            return e["_id"]
    return data["environments"][0]["_id"]


def update_variables(api_key: str, service_id: str, env_id: str, variables: dict[str, str]):
    """先 create，已存在則 update。"""
    for key, value in variables.items():
        try:
            gql(
                api_key,
                """
                mutation Create($svcID: ObjectID!, $envID: ObjectID!, $key: String!, $value: String!) {
                  createEnvironmentVariable(
                    serviceID: $svcID, environmentID: $envID, key: $key, value: $value
                  ) { key }
                }
                """,
                {"svcID": service_id, "envID": env_id, "key": key, "value": value},
            )
            print(f"  ✓ created {key}")
        except SystemExit as e:
            if "VARIABLE_ALREADY_EXISTS" in str(e):
                gql(
                    api_key,
                    """
                    mutation Update($svcID: ObjectID!, $envID: ObjectID!, $oldKey: String!, $newKey: String!, $value: String!) {
                      updateSingleEnvironmentVariable(
                        serviceID: $svcID, environmentID: $envID,
                        oldKey: $oldKey, newKey: $newKey, value: $value
                      ) { key }
                    }
                    """,
                    {
                        "svcID": service_id,
                        "envID": env_id,
                        "oldKey": key,
                        "newKey": key,
                        "value": value,
                    },
                )
                print(f"  ✓ updated {key}")
            else:
                raise


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bot")
    ap.add_argument("--project", default="KD-wecom")
    args = ap.parse_args()

    load_env()
    api_key = os.environ.get("ZEABUR_KEY") or os.environ.get("ZEABUR_API_KEY")
    if not api_key:
        raise SystemExit("ZEABUR_KEY not set")

    registry = BotRegistry.load(REPO_ROOT / "services" / "zeabur-gateway" / "bots")
    bot = registry.by_name(args.bot)

    # 從 .env 讀 5 個密鑰
    try:
        secrets_map = bot.env_vars_from_environ()
    except KeyError as e:
        raise SystemExit(str(e))

    proj = find_project(api_key, args.project)
    if not proj:
        raise SystemExit(f"project '{args.project}' not found — run deploy-once.py first")
    svc = find_service(api_key, proj["_id"], bot.zeabur_service_name)
    if not svc:
        raise SystemExit(f"service '{bot.zeabur_service_name}' not found")

    env_id = get_environment_id(api_key, proj["_id"])

    print(f"Syncing {len(secrets_map)} variables to {bot.zeabur_service_name} ...")
    for k in secrets_map:
        print(f"  - {k}")
    update_variables(api_key, svc["_id"], env_id, secrets_map)

    # 觸發 redeploy 讓變數生效
    print()
    print("→ Triggering redeploy ...")
    try:
        gql(
            api_key,
            """
            mutation R($svcID: ObjectID!, $envID: ObjectID!) {
              restartService(serviceID: $svcID, environmentID: $envID)
            }
            """,
            {"svcID": svc["_id"], "envID": env_id},
        )
        print("✓ Restart triggered")
    except SystemExit as e:
        print(f"⚠ Could not auto-restart: {e}")
        print("  Manually restart in Zeabur Dashboard")

    print()
    print("✓ Done. Variables synced.")
    print(f"  Wait ~30s for redeploy, then test:")
    print(f"  curl -sS https://{bot.domain}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
