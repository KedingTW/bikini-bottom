"""🐌 OpenAI Usage API 查詢層

使用 OpenAI Admin API 查詢：
- /v1/organization/usage/completions — token 用量（按 model/project 彙整）
- /v1/organization/costs — 每日費用明細

需要 Admin API Key（非一般 sk- key），在 OpenAI Platform → Admin keys 建立。
"""
import logging
import os
from datetime import datetime, timedelta, timezone

import httpx

OPENAI_API_KEY = os.environ.get("OPENAI_ADMIN_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.environ.get("OPENAI_ORG_ID", "")
BASE_URL = "https://api.openai.com/v1/organization"


def _headers() -> dict:
    h = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENAI_ORG_ID:
        h["OpenAI-Organization"] = OPENAI_ORG_ID
    return h


def _ts(dt) -> int:
    """datetime → Unix timestamp (int)"""
    if isinstance(dt, datetime):
        return int(dt.timestamp())
    return int(dt.replace(tzinfo=timezone.utc).timestamp()) if hasattr(dt, "replace") else int(dt)


# ─── 日期範圍工具 ──────────────────────────────────────────

def parse_openai_range(range_str: str | None) -> dict:
    """
    解析 range 參數：
    - None / "7" / "7d"  → 過去 7 天
    - "30" / "30d"       → 過去 30 天
    - "today"            → 今天
    - "month"            → 本月 1 日至今
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if not range_str:
        range_str = "7d"

    r = range_str.strip().lower()

    if r == "today":
        return {"start": today_start, "end": now, "label": "今日"}
    elif r == "month":
        month_start = today_start.replace(day=1)
        return {"start": month_start, "end": now, "label": f"{month_start.strftime('%m/%d')}~今日"}
    else:
        # 數字 or "Nd"
        days = int(r.replace("d", ""))
        start = today_start - timedelta(days=days)
        return {"start": start, "end": now, "label": f"過去 {days} 天"}


# ─── Costs 查詢 ───────────────────────────────────────────

async def query_costs(range_str: str | None = None) -> dict:
    """
    查詢 OpenAI 費用明細。
    回傳 {label, total_cost, by_model: [{model, cost}], by_day: [{date, cost}]}
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("未設定 OPENAI_ADMIN_KEY 或 OPENAI_API_KEY 環境變數")

    r = parse_openai_range(range_str)
    start_ts = _ts(r["start"])

    all_results = []
    page_token = None

    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            if page_token:
                # pagination: only pass the page token, no other params
                url = f"{BASE_URL}/costs?page={page_token}"
                resp = await client.get(url, headers=_headers())
            else:
                params = {
                    "start_time": start_ts,
                    "bucket_width": "1d",
                    "limit": 31,
                }
                resp = await client.get(
                    f"{BASE_URL}/costs",
                    headers=_headers(),
                    params=params,
                )

            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI Costs API 回傳 {resp.status_code}: {resp.text[:200]}")

            data = resp.json()
            all_results.extend(data.get("data", []))

            if data.get("has_more") and data.get("next_page"):
                page_token = data["next_page"]
            else:
                break

    # 彙整
    total_cost = 0.0
    by_model = {}
    by_day = {}

    for bucket in all_results:
        bucket_date = datetime.fromtimestamp(bucket["start_time"], tz=timezone.utc).strftime("%m/%d")
        for result in bucket.get("results", []):
            amount = float(result.get("amount", {}).get("value", 0) or 0)
            total_cost += amount
            line_item = result.get("line_item", "unknown")

            by_model.setdefault(line_item, 0.0)
            by_model[line_item] += amount

            by_day.setdefault(bucket_date, 0.0)
            by_day[bucket_date] += amount

    return {
        "label": r["label"],
        "total_cost": round(total_cost, 4),
        "by_model": sorted(
            [{"model": k, "cost": round(v, 4)} for k, v in by_model.items()],
            key=lambda x: x["cost"],
            reverse=True,
        ),
        "by_day": [{"date": k, "cost": round(v, 4)} for k, v in sorted(by_day.items())],
    }


# ─── Completions Usage 查詢 ───────────────────────────────

async def query_completions_usage(range_str: str | None = None) -> dict:
    """
    查詢 completions token 用量。
    回傳 {label, total_requests, total_input_tokens, total_output_tokens, by_model: [...]}
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("未設定 OPENAI_ADMIN_KEY 或 OPENAI_API_KEY 環境變數")

    r = parse_openai_range(range_str)
    start_ts = _ts(r["start"])

    all_results = []
    page_token = None

    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            if page_token:
                url = f"{BASE_URL}/usage/completions?page={page_token}"
                resp = await client.get(url, headers=_headers())
            else:
                params = {
                    "start_time": start_ts,
                    "bucket_width": "1d",
                    "group_by[]": "model",
                    "limit": 31,
                }
                resp = await client.get(
                    f"{BASE_URL}/usage/completions",
                    headers=_headers(),
                    params=params,
                )

            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI Usage API 回傳 {resp.status_code}: {resp.text[:200]}")

            data = resp.json()
            all_results.extend(data.get("data", []))

            if data.get("has_more") and data.get("next_page"):
                page_token = data["next_page"]
            else:
                break

    # 彙整
    total_input = 0
    total_output = 0
    total_requests = 0
    by_model = {}

    for bucket in all_results:
        for result in bucket.get("results", []):
            inp = result.get("input_tokens", 0) or 0
            out = result.get("output_tokens", 0) or 0
            reqs = result.get("num_model_requests", 0) or 0
            model = result.get("model", "unknown")

            total_input += inp
            total_output += out
            total_requests += reqs

            if model not in by_model:
                by_model[model] = {"input_tokens": 0, "output_tokens": 0, "requests": 0}
            by_model[model]["input_tokens"] += inp
            by_model[model]["output_tokens"] += out
            by_model[model]["requests"] += reqs

    return {
        "label": r["label"],
        "total_requests": total_requests,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "by_model": sorted(
            [{"model": k, **v} for k, v in by_model.items()],
            key=lambda x: x["input_tokens"] + x["output_tokens"],
            reverse=True,
        ),
    }
