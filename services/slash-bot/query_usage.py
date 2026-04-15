"""查詢 Kiro Usage (day-1 ~ day-30)，結果快取到 S3 JSON"""
import json
import time
from datetime import datetime, timedelta, timezone

import boto3

REGION = "us-east-1"
DATABASE = "kiro_usage"
TABLE = "user_report"
WORKGROUP = "kiro-usage"
CACHE_BUCKET = "keding-kiro-user-activity-report-us-east-1"
CACHE_PREFIX = "kiro-usage-cache/"

USER_MAP = {
    "0704fae8-c031-701c-38a9-fe8c6c0e32c5": "MinChe Tsai",
    "37943aa8-9011-7067-cdcc-d548211de86a": "sherry li",
    "97f42a28-00c1-70db-d2fe-fbc99d9278c1": "Hsuan Wu",
    "f7040a28-80d1-7029-e9a2-ce35b6c55b5b": "wahow chen",
}

s3 = boto3.client("s3", region_name=REGION)
athena = boto3.client("athena", region_name=REGION)


def get_cache_key():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{CACHE_PREFIX}{today}.json"


def read_cache():
    try:
        resp = s3.get_object(Bucket=CACHE_BUCKET, Key=get_cache_key())
        return json.loads(resp["Body"].read())
    except s3.exceptions.NoSuchKey:
        return None


def write_cache(data):
    s3.put_object(
        Bucket=CACHE_BUCKET,
        Key=get_cache_key(),
        Body=json.dumps(data, ensure_ascii=False, indent=2),
        ContentType="application/json",
    )


def run_athena_query():
    today = datetime.now(timezone.utc).date()
    d1 = today - timedelta(days=1)
    d30 = today - timedelta(days=30)

    # 用 partition 欄位篩選，避免全表掃描
    sql = f"""
    SELECT date, userid, client_type, subscription_tier,
           CAST(credits_used AS double) AS credits_used,
           CAST(total_messages AS bigint) AS total_messages,
           CAST(chat_conversations AS bigint) AS chat_conversations
    FROM {DATABASE}.{TABLE}
    WHERE year BETWEEN '{d30.year}' AND '{d1.year}'
      AND CAST(year || month || day AS integer)
          BETWEEN {d30.strftime('%Y%m%d')} AND {d1.strftime('%Y%m%d')}
    ORDER BY date DESC, userid
    """

    resp = athena.start_query_execution(QueryString=sql, WorkGroup=WORKGROUP)
    qid = resp["QueryExecutionId"]

    while True:
        status = athena.get_query_execution(QueryExecutionId=qid)
        state = status["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)

    if state != "SUCCEEDED":
        reason = status["QueryExecution"]["Status"].get("StateChangeReason", "")
        raise RuntimeError(f"Athena 查詢失敗: {state} - {reason}")

    rows = []
    paginator = athena.get_paginator("get_query_results")
    first_page = True
    for page in paginator.paginate(QueryExecutionId=qid):
        page_rows = page["ResultSet"]["Rows"]
        if first_page:
            page_rows = page_rows[1:]  # 跳過 header
            first_page = False
        for row in page_rows:
            vals = [col.get("VarCharValue", "") for col in row["Data"]]
            rows.append({
                "date": vals[0],
                "user": USER_MAP.get(vals[1], vals[1]),
                "client_type": vals[2],
                "tier": vals[3],
                "credits_used": round(float(vals[4]), 2) if vals[4] else 0,
                "total_messages": int(vals[5]) if vals[5] else 0,
                "chat_conversations": int(vals[6]) if vals[6] else 0,
            })
    return rows


def print_report(data):
    print(f"\n{'日期':<14} {'使用者':<16} {'額度消耗':>10} {'訊息數':>8} {'對話數':>8} {'方案':<10}")
    print("-" * 72)
    for r in data:
        print(f"{r['date']:<14} {r['user']:<16} {r['credits_used']:>10.2f} {r['total_messages']:>8} {r['chat_conversations']:>8} {r['tier']:<10}")


def main():
    print("🧽 查詢 Kiro 使用量 (day-1 ~ day-30)...\n")

    data = read_cache()
    if data:
        print("⚡ 使用快取資料")
    else:
        print("🔍 執行 Athena 查詢...")
        data = run_athena_query()
        write_cache(data)
        print("💾 已快取結果")

    print_report(data)
    print(f"\n🍔 共 {len(data)} 筆資料")
    return data


if __name__ == "__main__":
    main()
