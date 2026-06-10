#!/usr/bin/env python3
"""
一次性部署：在 Zeabur 上建 bikini-bottom project + 為指定 bot 建 gateway service。

用法：
    ZEABUR_KEY=sk-... python services/zeabur-gateway/scripts/deploy-once.py order-transform
    （會讀 .env 中 ZEABUR_KEY 或 ZEABUR_API_KEY）

輸出：
    - 新建 project / service ID
    - service 的預設 Zeabur domain（用來掛 CNAME）

冪等：跑第二次會偵測已存在的 project 並 skip。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
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
        "User-Agent": "bikini-bottom-zeabur-deploy/1.0",
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
    """name 比對 case-insensitive（Zeabur 自動把 project name 轉小寫）。"""
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
        query Services($projectID: ObjectID!) {
          services(projectID: $projectID) {
            edges { node { _id name } }
          }
        }
        """,
        {"projectID": project_id},
    )
    for e in data["services"]["edges"]:
        if e["node"]["name"] == name:
            return e["node"]
    return None


def domain_for_service(api_key: str, project_id: str, service_id: str) -> str | None:
    """讀 service 的預設 zeabur domain。"""
    data = gql(
        api_key,
        """
        query SvcDomain($svcID: ObjectID!) {
          service(_id: $svcID) {
            _id
            name
            domains { domain isGenerated }
          }
        }
        """,
        {"svcID": service_id},
    )
    svc = data.get("service") or {}
    domains = svc.get("domains") or []
    if not domains:
        return None
    # 優先回傳系統產生的（*.zeabur.app）
    for d in domains:
        if d.get("isGenerated"):
            return d["domain"]
    return domains[0]["domain"]


def get_environment_id(api_key: str, project_id: str) -> str:
    """取得 production environment ID。"""
    data = gql(
        api_key,
        """
        query Envs($projectID: ObjectID!) {
          environments(projectID: $projectID) { _id name }
        }
        """,
        {"projectID": project_id},
    )
    envs = data["environments"]
    for e in envs:
        if e["name"] == "production":
            return e["_id"]
    return envs[0]["_id"]


def add_domain(api_key: str, service_id: str, env_id: str, domain: str, is_generated: bool):
    """加 generated domain（gateway-order-transform.zeabur.app）或 custom domain。"""
    return gql(
        api_key,
        """
        mutation AddDomain($svcID: ObjectID!, $envID: ObjectID!, $domain: String!, $isGenerated: Boolean!) {
          addDomain(serviceID: $svcID, environmentID: $envID, domain: $domain, isGenerated: $isGenerated) {
            domain
            isGenerated
          }
        }
        """,
        {"svcID": service_id, "envID": env_id, "domain": domain, "isGenerated": is_generated},
    )["addDomain"]


def deploy_template(api_key: str, project_name: str, bot, project_id: str | None) -> dict:
    yaml_spec = f"""
apiVersion: zeabur.com/v1
kind: Template
metadata:
  name: {project_name}
spec:
  description: WeCom bots gateway cluster — managed by services/zeabur-gateway
  services:
    - name: {bot.zeabur_service_name}
      template: PREBUILT_V2
      spec:
        source:
          image: ghcr.io/openabdev/openab-gateway:latest
        ports:
          - id: web
            port: 8080
            type: HTTP
        env:
          WECOM_CORP_ID: {{ default: "" }}
          WECOM_AGENT_ID: {{ default: "" }}
          WECOM_SECRET: {{ default: "" }}
          WECOM_TOKEN: {{ default: "" }}
          WECOM_ENCODING_AES_KEY: {{ default: "" }}
""".strip()
    data = gql(
        api_key,
        """
        mutation DeployTemplate($rawSpecYaml: String, $projectID: ObjectID) {
          deployTemplate(rawSpecYaml: $rawSpecYaml, projectID: $projectID) { _id }
        }
        """,
        {"rawSpecYaml": yaml_spec, "projectID": project_id},
    )
    return data["deployTemplate"]


def create_project(api_key: str, name: str, region: str) -> dict:
    """建立空 project（指定 region）。"""
    data = gql(
        api_key,
        """
        mutation CreateProject($name: String!, $region: String!) {
          createProject(name: $name, region: $region) { _id name }
        }
        """,
        {"name": name, "region": region},
    )
    return data["createProject"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bot", help="bot name (e.g. order)")
    ap.add_argument("--project", default="KD-wecom", help="Zeabur project 名稱")
    ap.add_argument(
        "--region",
        default="server-6a0ab459583c6565f8073589",
        help="Zeabur region/server ID（預設 = 既有 Lightsail Tokyo server）",
    )
    args = ap.parse_args()

    load_env()
    api_key = os.environ.get("ZEABUR_KEY") or os.environ.get("ZEABUR_API_KEY")
    if not api_key:
        raise SystemExit("ZEABUR_KEY (or ZEABUR_API_KEY) not set in .env")

    registry = BotRegistry.load(REPO_ROOT / "services" / "zeabur-gateway" / "bots")
    bot = registry.by_name(args.bot)
    print(f"Bot: {bot.name} ({bot.display_name})")
    print(f"Service: {bot.zeabur_service_name}")
    print(f"Image: ghcr.io/openabdev/openab-gateway:latest")
    print()

    # 1. project — 先建空的
    proj = find_project(api_key, args.project)
    if proj:
        print(f"✓ Project '{args.project}' exists: {proj['_id']}")
    else:
        print(f"→ Creating project '{args.project}' in region '{args.region}' ...")
        proj = create_project(api_key, args.project, args.region)
        print(f"✓ Project created: {proj['_id']}")

    # 2. service — 透過 deployTemplate 帶 projectID
    svc = find_service(api_key, proj["_id"], bot.zeabur_service_name)
    if svc:
        print(f"✓ Service '{bot.zeabur_service_name}' exists: {svc['_id']}")
    else:
        print(f"→ Deploying service '{bot.zeabur_service_name}' via template ...")
        deploy_template(api_key, args.project, bot, proj["_id"])
        # 讀回 service id
        import time
        for _ in range(10):
            time.sleep(2)
            svc = find_service(api_key, proj["_id"], bot.zeabur_service_name)
            if svc:
                break
        if not svc:
            raise SystemExit("Service did not appear within 20s — check Zeabur dashboard")
        print(f"✓ Service deployed: {svc['_id']}")

    # 3. domains（generated + custom）
    env_id = get_environment_id(api_key, proj["_id"])
    existing = domain_for_service(api_key, proj["_id"], svc["_id"])
    domains_have = set()
    if existing:
        # 重新拉一次完整列表
        data = gql(
            api_key,
            "query($id: ObjectID!){ service(_id:$id){ domains{ domain isGenerated } } }",
            {"id": svc["_id"]},
        )
        for d in (data.get("service") or {}).get("domains") or []:
            domains_have.add(d["domain"])

    # 系統 domain：用 service 名（會自動補 .zeabur.app）
    generated_short = bot.zeabur_service_name
    generated_full = f"{generated_short}.zeabur.app"
    if generated_full not in domains_have:
        print(f"→ Adding generated domain: {generated_full}")
        try:
            add_domain(api_key, svc["_id"], env_id, generated_short, True)
        except SystemExit as e:
            print(f"⚠ skip generated domain: {e}")

    # 自家 domain
    if bot.domain not in domains_have:
        print(f"→ Adding custom domain: {bot.domain}")
        try:
            add_domain(api_key, svc["_id"], env_id, bot.domain, False)
        except SystemExit as e:
            print(f"⚠ skip custom domain: {e}")

    # 4. 印出結果
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Project:       {proj['name']} ({proj['_id']})")
    print(f"Service:       {svc['name']} ({svc['_id']})")
    print(f"Zeabur domain: https://{generated_full}")
    print(f"Custom domain: https://{bot.domain}")
    print()
    print(f"Next steps:")
    print(f"  1. DNS：{bot.domain}.  CNAME  {generated_full}.")
    print(f"  2. Zeabur Dashboard → service '{bot.zeabur_service_name}' → Variables：填 5 個 WECOM_* 密鑰")
    print(f"  3. WeCom 後台 callback URL: {bot.webhook_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
