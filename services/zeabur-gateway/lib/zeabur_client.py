"""
Zeabur GraphQL API client.

封裝 Zeabur 的 service 部署、環境變數、domain 操作。
未來 admin 也會用這支模組。

Reference:
- API endpoint: https://api.zeabur.com/graphql
- Auth: Bearer <ZEABUR_API_KEY>
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any
from urllib import request as _urllib_request
from urllib.error import HTTPError, URLError


ZEABUR_API_URL = "https://api.zeabur.com/graphql"


class ZeaburError(Exception):
    """Zeabur API 操作失敗。"""


@dataclass
class ZeaburClient:
    """
    Zeabur GraphQL 客戶端（最小可用版本）。

    用法：
        client = ZeaburClient(api_key=os.environ["ZEABUR_API_KEY"])
        client.upsert_service(...)

    未來 admin web UI 直接 import 這個 class 即可。
    """

    api_key: str
    project_id: str | None = None
    timeout: int = 30
    _last_response: dict[str, Any] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ZeaburError("ZEABUR_API_KEY is required")

    # ─── Low-level GraphQL ────────────────────────────────────
    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """執行 GraphQL 查詢/突變。失敗會 raise ZeaburError。"""
        payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        req = _urllib_request.Request(
            ZEABUR_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with _urllib_request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            raise ZeaburError(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}") from exc
        except URLError as exc:
            raise ZeaburError(f"network error: {exc.reason}") from exc

        self._last_response = body
        if body.get("errors"):
            raise ZeaburError(json.dumps(body["errors"], ensure_ascii=False))
        return body.get("data") or {}

    # ─── Service CRUD ────────────────────────────────────────
    def list_projects(self) -> list[dict[str, Any]]:
        """列出帳號下所有 project。"""
        data = self.graphql(
            """
            query Projects {
              projects {
                _id
                name
              }
            }
            """
        )
        return data.get("projects") or []

    def list_services(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """列出 project 內所有 service。"""
        pid = project_id or self.project_id
        if not pid:
            raise ZeaburError("project_id is required")
        data = self.graphql(
            """
            query Services($projectID: ObjectID!) {
              services(projectID: $projectID) {
                _id
                name
                template
              }
            }
            """,
            {"projectID": pid},
        )
        return data.get("services") or []

    def find_service_by_name(self, name: str, project_id: str | None = None) -> dict[str, Any] | None:
        for svc in self.list_services(project_id):
            if svc.get("name") == name:
                return svc
        return None

    def create_service_from_image(
        self,
        name: str,
        image: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """
        以 prebuilt image 建立 service。
        對 OpenAB Gateway 場景：image = ghcr.io/openabdev/openab-gateway:latest
        """
        pid = project_id or self.project_id
        if not pid:
            raise ZeaburError("project_id is required")
        data = self.graphql(
            """
            mutation CreateService($projectID: ObjectID!, $name: String!, $template: String!) {
              createService(projectID: $projectID, name: $name, template: $template) {
                _id
                name
              }
            }
            """,
            {"projectID": pid, "name": name, "template": "PREBUILT_V2"},
        )
        svc = data.get("createService")
        if not svc:
            raise ZeaburError("createService returned empty result")
        # 以 prebuilt image spec 更新 service
        self.update_service_spec(svc["_id"], {"source": {"image": image}})
        return svc

    def update_service_spec(self, service_id: str, spec: dict[str, Any]) -> None:
        """更新 service spec（image / port / 等）。"""
        # NOTE: 實際 mutation 名稱依 Zeabur API 而定，這裡保留為待補
        # 待第一次手動部署成功後，從 Zeabur dashboard 觀察 GraphQL 請求補完
        raise NotImplementedError(
            "update_service_spec: pending — see docs/wecom-zeabur-setup.md for manual fallback"
        )

    # ─── Environment Variables ───────────────────────────────
    def upsert_env(self, service_id: str, env_id: str, variables: dict[str, str]) -> None:
        """設定 service 的環境變數（覆蓋同名）。"""
        # NOTE: 同上，待補。CLI 階段先以手動 dashboard 設定為主。
        raise NotImplementedError(
            "upsert_env: pending — see docs/wecom-zeabur-setup.md for manual fallback"
        )

    # ─── Domain ──────────────────────────────────────────────
    def add_custom_domain(self, service_id: str, domain: str) -> None:
        """綁定自家 domain 到 service。"""
        raise NotImplementedError(
            "add_custom_domain: pending — see docs/wecom-zeabur-setup.md for manual fallback"
        )
