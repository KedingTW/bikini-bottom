"""Key Pool Coordinator — Kiro API Key 自動輪替模組"""
import os
import re
import logging
import subprocess
import threading
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────
TZ_TAIPEI = timezone(timedelta(hours=8))
ALERT_THRESHOLD_PERCENT = int(os.environ.get("KEY_POOL_ALERT_THRESHOLD", "80"))
ALERT_REMAINING_KEYS = int(os.environ.get("KEY_POOL_ALERT_REMAINING", "0"))
ALERT_CHANNEL_ID = os.environ.get("KEY_POOL_ALERT_CHANNEL", "1493802266296188988")
USAGE_CHECK_INTERVAL_HOURS = int(os.environ.get("KEY_POOL_USAGE_INTERVAL", "1"))

router = APIRouter()

# ─── DB helper (lazy import from app) ─────────────────────
_get_db = None


def _init_module(get_db_func):
    """由 app.py 呼叫，注入 get_db 函式。"""
    global _get_db
    _get_db = get_db_func
    _init_key_pool_tables()


def _db():
    """取得 DB 連線。"""
    if _get_db is None:
        raise RuntimeError("key_pool module not initialized, call _init_module(get_db) first")
    return _get_db()


# ─── DB Init ──────────────────────────────────────────────
def _init_key_pool_tables():
    """建立 key pool 相關表（如果不存在）。"""
    conn = _db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS key_pool (
                id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                key_name        VARCHAR(50)  NOT NULL UNIQUE COMMENT '識別名稱，如 POOL_01',
                key_value       VARCHAR(255) NOT NULL COMMENT '實際 Kiro API Key 值',
                priority        INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '使用順序，數字小的優先',
                enabled         TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否啟用',
                exhausted_until DATETIME     NULL DEFAULT NULL COMMENT 'NULL=可用；有值=耗盡到該時間',
                exhausted_reason VARCHAR(100) NULL DEFAULT NULL COMMENT '耗盡原因',
                pick_count      INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累計被挑選次數',
                last_picked_at  DATETIME     NULL DEFAULT NULL COMMENT '最近被挑選時間',
                last_picked_by  VARCHAR(50)  NULL DEFAULT NULL COMMENT '最近被哪個 agent 挑選',
                last_usage_percent DECIMAL(5,2) NULL DEFAULT NULL COMMENT '最近用量百分比',
                last_usage_checked_at DATETIME NULL DEFAULT NULL COMMENT '最近用量查詢時間',
                note            VARCHAR(255) NULL DEFAULT NULL COMMENT '備註',
                created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_pick (enabled, exhausted_until, priority)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
              COMMENT='Kiro API Key 池'
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS key_usage_history (
                id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                key_name     VARCHAR(50)  NOT NULL COMMENT '對應 key_pool.key_name',
                used_percent DECIMAL(5,2) NULL COMMENT '用量百分比',
                raw_response TEXT         NULL COMMENT '/usage 原始回傳',
                checked_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_key_time (key_name, checked_at DESC)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
              COMMENT='Key 用量歷史紀錄'
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pick_log (
                id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                key_name  VARCHAR(50) NOT NULL COMMENT '被挑選的 key',
                agent     VARCHAR(50) NOT NULL COMMENT '請求的 agent',
                picked_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_time (picked_at DESC),
                INDEX idx_agent (agent, picked_at DESC)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
              COMMENT='Key 挑選紀錄'
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS exhausted_log (
                id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                key_name        VARCHAR(50)  NOT NULL COMMENT '被標記的 key',
                reason          VARCHAR(100) NULL COMMENT '耗盡原因',
                agent           VARCHAR(50)  NULL COMMENT '回報的 agent',
                marked_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                exhausted_until DATETIME     NULL COMMENT '預計恢復時間',
                INDEX idx_key_time (key_name, marked_at DESC)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
              COMMENT='Key 耗盡事件紀錄'
        """)
        conn.commit()
    except Exception as e:
        logger.error(f"[key_pool] init tables failed: {e}")
    finally:
        conn.close()


# ─── Request Models ───────────────────────────────────────
class PickRequest(BaseModel):
    agent: str


class MarkRequest(BaseModel):
    key_name: str
    reason: Optional[str] = None
    agent: Optional[str] = None
    exhausted_until: Optional[str] = None  # ISO format, caller 可覆寫 reset 時間


# ─── API Routes ───────────────────────────────────────────
@router.post("/pick")
async def pick_key(req: PickRequest):
    """Sequential drain：取得優先序最高的可用 key。"""
    conn = _db()
    try:
        cur = conn.cursor()

        # 找可用 key（未耗盡 or 已過恢復時間）
        # Sequential drain：找優先序最高的可用 key。
        # 多個 agent 併發 pick 會拿到同一把 key — 這是 by design。
        # 策略是「同一把用到滿再換下一把」，不做 round-robin。
        cur.execute("""
            SELECT id, key_name, key_value, priority
            FROM key_pool
            WHERE enabled = 1
              AND (exhausted_until IS NULL OR exhausted_until < NOW())
            ORDER BY priority ASC
            LIMIT 1
        """)
        row = cur.fetchone()

        if row:
            key_id, key_name, key_value, priority = row

            # 更新 pick 統計
            cur.execute("""
                UPDATE key_pool
                SET pick_count = pick_count + 1, last_picked_at = NOW(), last_picked_by = %s
                WHERE id = %s
            """, (req.agent, key_id))

            # 寫 pick log
            cur.execute("""
                INSERT INTO pick_log (key_name, agent, picked_at)
                VALUES (%s, %s, NOW())
            """, (key_name, req.agent))

            conn.commit()
            return {"key_name": key_name, "key_value": key_value, "priority": priority}

        # 全耗盡：回傳最接近 reset 的那把作為 fallback
        cur.execute("""
            SELECT key_name, priority, exhausted_until
            FROM key_pool
            WHERE enabled = 1
            ORDER BY exhausted_until ASC
            LIMIT 1
        """)
        fallback = cur.fetchone()

        if fallback:
            fb_name, fb_priority, fb_until = fallback
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "all_exhausted",
                    "message": "所有 key 都已耗盡，wrap 應使用本地 fallback",
                },
            )

        # 完全沒有任何 key
        raise HTTPException(status_code=503, detail={"error": "no_keys", "message": "Pool 中沒有任何 key"})

    finally:
        conn.close()


@router.post("/mark")
async def mark_key(req: MarkRequest):
    """標記 key 為耗盡。exhausted_until 可由 caller 指定，否則預設下個月 1 號。"""
    conn = _db()
    try:
        cur = conn.cursor()

        # 確認 key 存在
        cur.execute("SELECT id FROM key_pool WHERE key_name = %s", (req.key_name,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"key {req.key_name} 不存在"})

        # 決定 reset 時間：caller 指定 > 預設下個月 1 號
        if req.exhausted_until:
            try:
                reset_time = datetime.fromisoformat(req.exhausted_until)
            except ValueError:
                raise HTTPException(status_code=400, detail={"error": "invalid_date", "message": "exhausted_until 格式不正確，請用 ISO format"})
        else:
            # 預設：下個月 1 號 00:00 UTC+8
            now = datetime.now(TZ_TAIPEI)
            if now.month == 12:
                reset_time = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                reset_time = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # 更新 key_pool
        cur.execute("""
            UPDATE key_pool
            SET exhausted_until = %s, exhausted_reason = %s, updated_at = NOW()
            WHERE key_name = %s
        """, (reset_time.strftime("%Y-%m-%d %H:%M:%S"), req.reason, req.key_name))

        # 寫 exhausted_log
        cur.execute("""
            INSERT INTO exhausted_log (key_name, reason, agent, marked_at, exhausted_until)
            VALUES (%s, %s, %s, NOW(), %s)
        """, (req.key_name, req.reason, req.agent, reset_time.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()

        # 觸發告警檢查（非同步，不阻塞回應）
        threading.Thread(target=_check_and_alert, daemon=True).start()

        return {
            "key_name": req.key_name,
            "exhausted_until": reset_time.isoformat(),
            "message": f"已標記為耗盡，預計 {reset_time.strftime('%Y-%m-%d')} 恢復",
        }

    finally:
        conn.close()


@router.get("/state")
async def pool_state():
    """查看 pool 即時狀態。"""
    conn = _db()
    try:
        cur = conn.cursor()

        # 所有 key
        cur.execute("""
            SELECT key_name, priority, enabled, exhausted_until, exhausted_reason,
                   pick_count, last_picked_at, last_picked_by,
                   last_usage_percent, last_usage_checked_at, note
            FROM key_pool
            ORDER BY priority ASC
        """)
        rows = cur.fetchall()

        keys = []
        total = 0
        available = 0
        exhausted = 0
        current_key = None
        now = datetime.now(TZ_TAIPEI)

        for row in rows:
            (name, priority, enabled, exh_until, exh_reason,
             pick_count, last_picked, last_picked_by,
             usage_pct, usage_checked, note) = row

            total += 1
            is_available = (
                enabled == 1
                and (exh_until is None or exh_until < now.replace(tzinfo=None))
            )

            if is_available:
                available += 1
                if current_key is None:
                    current_key = {
                        "key_name": name,
                        "priority": priority,
                        "pick_count": pick_count,
                        "last_usage_percent": float(usage_pct) if usage_pct is not None else None,
                        "last_usage_checked_at": usage_checked.isoformat() if usage_checked else None,
                    }
            else:
                exhausted += 1

            keys.append({
                "key_name": name,
                "priority": priority,
                "enabled": bool(enabled),
                "exhausted_until": exh_until.isoformat() if exh_until else None,
                "exhausted_reason": exh_reason,
                "pick_count": pick_count,
                "last_picked_at": last_picked.isoformat() if last_picked else None,
                "last_picked_by": last_picked_by,
                "last_usage_percent": float(usage_pct) if usage_pct is not None else None,
                "last_usage_checked_at": usage_checked.isoformat() if usage_checked else None,
                "note": note,
            })

        return {
            "total_keys": total,
            "available_keys": available,
            "exhausted_keys": exhausted,
            "current_key": current_key,
            "keys": keys,
        }

    finally:
        conn.close()


@router.post("/check-usage")
async def check_usage_now():
    """手動觸發用量查詢（同步執行，等結果回傳）。"""
    import shutil

    if not shutil.which("kiro-cli"):
        raise HTTPException(status_code=503, detail={"error": "kiro_cli_not_found", "message": "kiro-cli 未安裝"})

    conn = _db()
    results = []
    try:
        cur = conn.cursor()
        cur.execute("SELECT key_name, key_value FROM key_pool WHERE enabled = 1")
        keys = cur.fetchall()

        for key_name, key_value in keys:
            used_percent = None
            try:
                check_env = {**os.environ, "KIRO_API_KEY": key_value}
                check_env.pop("KEY_POOL_URL", None)
                check_env.pop("FALLBACK_KIRO_KEY", None)

                result = subprocess.run(
                    ["kiro-cli", "chat", "--no-interactive", "/usage"],
                    env=check_env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                output = result.stdout + result.stderr
                used_percent = _parse_usage_output(output)

                # 存入歷史
                cur.execute("""
                    INSERT INTO key_usage_history (key_name, used_percent, raw_response, checked_at)
                    VALUES (%s, %s, %s, NOW())
                """, (key_name, used_percent, output[:2000]))

                # 更新 key_pool 快取欄位
                if used_percent is not None:
                    cur.execute("""
                        UPDATE key_pool
                        SET last_usage_percent = %s, last_usage_checked_at = NOW()
                        WHERE key_name = %s
                    """, (used_percent, key_name))

                    # 自動 mark：usage ≥ 100% 視為耗盡
                    if used_percent >= 100:
                        now_tp = datetime.now(TZ_TAIPEI)
                        if now_tp.month == 12:
                            reset_time = now_tp.replace(year=now_tp.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                        else:
                            reset_time = now_tp.replace(month=now_tp.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                        cur.execute("""
                            UPDATE key_pool
                            SET exhausted_until = %s, exhausted_reason = %s, updated_at = NOW()
                            WHERE key_name = %s AND (exhausted_until IS NULL OR exhausted_until < NOW())
                        """, (reset_time.strftime("%Y-%m-%d %H:%M:%S"), "usage-100-auto", key_name))
                        cur.execute("""
                            INSERT INTO exhausted_log (key_name, reason, agent, marked_at, exhausted_until)
                            VALUES (%s, %s, %s, NOW(), %s)
                        """, (key_name, "usage-100-auto", "manual-check", reset_time.strftime("%Y-%m-%d %H:%M:%S")))
                        logger.info(f"[key_pool] check-usage: {key_name} auto-marked exhausted")

            except subprocess.TimeoutExpired:
                logger.warning(f"[key_pool] check-usage: {key_name} timeout")
            except Exception as e:
                logger.error(f"[key_pool] check-usage: {key_name} error: {e}")

            results.append({"key_name": key_name, "used_percent": used_percent})

        conn.commit()
    finally:
        conn.close()

    # 告警判斷
    _check_and_alert()

    now = datetime.now(TZ_TAIPEI)
    return {"results": results, "checked_at": now.isoformat()}


# ─── Usage Check (排程) ───────────────────────────────────
def _parse_usage_output(output: str) -> Optional[float]:
    """解析 kiro-cli /usage 的輸出，取得用量百分比。"""
    # 嘗試匹配百分比模式，例如 "Usage: 45.2%" 或 "45.2/100" 或 "used 45.2%"
    patterns = [
        r'(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*/\s*\d+',
        r'used[:\s]+(\d+(?:\.\d+)?)',
    ]
    for pat in patterns:
        m = re.search(pat, output, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            if val >= 0:
                return val
    return None


def check_all_key_usage():
    """排程任務：逐一查詢所有啟用 key 的用量。"""
    logger.info("[key_pool] Starting usage check for all keys...")
    conn = _db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT key_name, key_value FROM key_pool WHERE enabled = 1")
        keys = cur.fetchall()

        for key_name, key_value in keys:
            try:
                # 建構 subprocess env：注入 key，移除 KEY_POOL_URL 避免意外觸發 wrap 遞迴
                check_env = {**os.environ, "KIRO_API_KEY": key_value}
                check_env.pop("KEY_POOL_URL", None)
                check_env.pop("FALLBACK_KIRO_KEY", None)

                result = subprocess.run(
                    ["kiro-cli", "chat", "--no-interactive", "/usage"],
                    env=check_env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                output = result.stdout + result.stderr
                used_percent = _parse_usage_output(output)

                # 存入歷史
                cur.execute("""
                    INSERT INTO key_usage_history (key_name, used_percent, raw_response, checked_at)
                    VALUES (%s, %s, %s, NOW())
                """, (key_name, used_percent, output[:2000]))

                # 更新 key_pool 快取欄位
                if used_percent is not None:
                    cur.execute("""
                        UPDATE key_pool
                        SET last_usage_percent = %s, last_usage_checked_at = NOW()
                        WHERE key_name = %s
                    """, (used_percent, key_name))

                    # 自動 mark：usage ≥ 100% 視為耗盡
                    if used_percent >= 100:
                        now = datetime.now(TZ_TAIPEI)
                        if now.month == 12:
                            reset_time = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                        else:
                            reset_time = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                        cur.execute("""
                            UPDATE key_pool
                            SET exhausted_until = %s, exhausted_reason = %s, updated_at = NOW()
                            WHERE key_name = %s AND (exhausted_until IS NULL OR exhausted_until < NOW())
                        """, (reset_time.strftime("%Y-%m-%d %H:%M:%S"), "usage-100-auto", key_name))
                        cur.execute("""
                            INSERT INTO exhausted_log (key_name, reason, agent, marked_at, exhausted_until)
                            VALUES (%s, %s, %s, NOW(), %s)
                        """, (key_name, "usage-100-auto", "scheduler", reset_time.strftime("%Y-%m-%d %H:%M:%S")))
                        logger.info(f"[key_pool] {key_name}: auto-marked exhausted (usage {used_percent}%)")

                logger.info(f"[key_pool] {key_name}: {used_percent}%")

            except subprocess.TimeoutExpired:
                logger.warning(f"[key_pool] {key_name}: usage check timeout")
            except Exception as e:
                logger.error(f"[key_pool] {key_name}: usage check error: {e}")

        conn.commit()
    except Exception as e:
        logger.error(f"[key_pool] check_all_key_usage error: {e}")
    finally:
        conn.close()

    # 告警判斷
    _check_and_alert()


def _check_and_alert():
    """檢查告警條件並發送 Discord 通知。"""
    conn = _db()
    try:
        cur = conn.cursor()

        # 計算可用 key 數（未耗盡的）
        cur.execute("""
            SELECT COUNT(*) FROM key_pool
            WHERE enabled = 1
              AND (exhausted_until IS NULL OR exhausted_until < NOW())
        """)
        available_count = cur.fetchone()[0]

        # 取得當前 key（優先序最高的可用 key）
        cur.execute("""
            SELECT key_name, last_usage_percent FROM key_pool
            WHERE enabled = 1
              AND (exhausted_until IS NULL OR exhausted_until < NOW())
            ORDER BY priority ASC
            LIMIT 1
        """)
        current = cur.fetchone()

        alerts = []

        if current and current[1] is not None:
            usage = float(current[1])
            # 告警 1：current key ≥ 80% 且剩餘可用 = 0（扣除自己就沒了）
            if usage >= ALERT_THRESHOLD_PERCENT and available_count <= 1:
                alerts.append(f"⚠️ 最後一把 key `{current[0]}` 用量已達 {current[1]}%，無備援 key")
            # 告警 2：current key ≥ 100%（已超額）
            if usage >= 100:
                alerts.append(f"🚨 Key `{current[0]}` 已超額使用中（{current[1]}%）")

        if alerts:
            _send_discord_alert("\n".join(alerts))

    except Exception as e:
        logger.error(f"[key_pool] alert check error: {e}")
    finally:
        conn.close()


def _send_discord_alert(message: str):
    """發送告警到 Discord 頻道。"""
    try:
        import httpx

        bot_token = os.environ.get("DISCORD_ADMIN_BOT_TOKEN", os.environ.get("DISCORD_BOT_TOKEN", ""))
        if not bot_token:
            logger.warning("[key_pool] No Discord bot token, skipping alert")
            return

        resp = httpx.post(
            f"https://discord.com/api/v10/channels/{ALERT_CHANNEL_ID}/messages",
            headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
            json={"content": f"🔑 **Key Pool Alert**\n{message}"},
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info(f"[key_pool] Alert sent: {message}")
        else:
            logger.warning(f"[key_pool] Alert send failed: {resp.status_code}")

    except Exception as e:
        logger.error(f"[key_pool] Discord alert error: {e}")


# ─── Usage 排程啟動 ───────────────────────────────────────
_usage_timer = None


def start_usage_scheduler():
    """啟動定期 usage check 排程。"""
    import shutil

    if not shutil.which("kiro-cli"):
        logger.warning("[key_pool] kiro-cli not found in PATH, usage check will be disabled")
        return

    global _usage_timer
    interval = USAGE_CHECK_INTERVAL_HOURS * 3600

    def _run():
        global _usage_timer
        try:
            check_all_key_usage()
        except Exception as e:
            logger.error(f"[key_pool] scheduler error: {e}")
        # 排下一次
        _usage_timer = threading.Timer(interval, _run)
        _usage_timer.daemon = True
        _usage_timer.start()

    # 延遲 60 秒後開始第一次（讓 app 先穩定啟動）
    _usage_timer = threading.Timer(60, _run)
    _usage_timer.daemon = True
    _usage_timer.start()
    logger.info(f"[key_pool] Usage scheduler started (interval: {USAGE_CHECK_INTERVAL_HOURS}h)")
