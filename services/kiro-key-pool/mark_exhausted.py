"""
mark_exhausted.py — 標記一把 key 為 exhausted（額度用完）
呼叫時需持有 flock。

參考 kiro-multi 的 passive learning：
- session 結束時偵測 stderr 的 quota 訊號
- 標記該 key 不再被 pick，直到 reset day
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def next_month_first() -> str:
    """計算下個月 1 號 00:00 UTC 作為 resets_at"""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        reset = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        reset = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return reset.isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True, help="state.json 路徑")
    parser.add_argument("--key-id", required=True, help="要標記的 key ID")
    parser.add_argument("--reason", default="", help="錯誤原因（stderr tail）")
    args = parser.parse_args()

    state_path = Path(args.state)
    if not state_path.exists():
        print(f"[mark_exhausted] state 檔案不存在: {args.state}", file=sys.stderr)
        sys.exit(1)

    with open(state_path) as f:
        state = json.load(f)

    if args.key_id not in state.get("keys", {}):
        print(f"[mark_exhausted] key_id '{args.key_id}' 不在 state 中", file=sys.stderr)
        sys.exit(1)

    key_state = state["keys"][args.key_id]
    key_state["exhausted"] = True
    key_state["resets_at"] = next_month_first()
    key_state["last_error"] = args.reason[:500] if args.reason else None
    key_state["exhausted_at"] = now_iso()

    with open(state_path, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(f"[mark_exhausted] key '{args.key_id}' 已標記 exhausted，resets_at={key_state['resets_at']}", file=sys.stderr)


if __name__ == "__main__":
    main()
