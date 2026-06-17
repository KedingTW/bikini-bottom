"""
pick.py — 從 key pool 中選一把可用的 key（round-robin）
輸出：key_id\tkey_value（tab 分隔）
呼叫時需持有 flock。

參考 kiro-multi pick policy：
- round-robin cursor
- 跳過 exhausted / cooldown 中的 key
- 所有 key 都不可用時輸出空字串並 exit 1
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_keys(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def load_state(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"schema_version": 1, "cursor": 0, "keys": {}}
    with open(p) as f:
        return json.load(f)


def save_state(path: str, state: dict):
    with open(path, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def is_available(key_state: dict) -> bool:
    """檢查一把 key 是否可用"""
    if key_state.get("exhausted"):
        # 檢查是否已過 reset day（每月 1 號自動解凍）
        resets_at = key_state.get("resets_at")
        if resets_at:
            reset_dt = datetime.fromisoformat(resets_at)
            if datetime.now(timezone.utc) >= reset_dt:
                # 自動解凍
                key_state["exhausted"] = False
                key_state["resets_at"] = None
                return True
        return False

    cooldown_until = key_state.get("cooldown_until")
    if cooldown_until:
        cd_dt = datetime.fromisoformat(cooldown_until)
        if datetime.now(timezone.utc) < cd_dt:
            return False
        # cooldown 已過
        key_state["cooldown_until"] = None

    return True


def pick(keys: list[dict], state: dict, agent: str) -> tuple[str, str] | None:
    """
    Round-robin 選一把可用的 key。
    回傳 (key_id, key_value) 或 None。
    """
    n = len(keys)
    if n == 0:
        return None

    cursor = state.get("cursor", 0) % n

    # 從 cursor 開始繞一圈
    for i in range(n):
        idx = (cursor + i) % n
        key_entry = keys[idx]
        key_id = key_entry["id"]

        # 確保 state 有這把 key 的紀錄
        if key_id not in state["keys"]:
            state["keys"][key_id] = {
                "exhausted": False,
                "cooldown_until": None,
                "resets_at": None,
                "last_picked_at": None,
                "pick_count": 0,
                "last_error": None,
            }

        key_state = state["keys"][key_id]

        if not is_available(key_state):
            continue

        # 選中！更新 state
        key_state["last_picked_at"] = now_iso()
        key_state["pick_count"] = key_state.get("pick_count", 0) + 1
        state["cursor"] = (idx + 1) % n  # 下次從下一把開始

        return key_id, key_entry["key"]

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keys", required=True, help="keys.json 路徑")
    parser.add_argument("--state", required=True, help="state.json 路徑")
    parser.add_argument("--agent", default="unknown", help="呼叫的 agent 名稱")
    args = parser.parse_args()

    keys = load_keys(args.keys)
    state = load_state(args.state)

    result = pick(keys, state, args.agent)

    if result is None:
        print("[pick] 所有 key 都不可用 (exhausted 或 cooldown)", file=sys.stderr)
        save_state(args.state, state)
        sys.exit(1)

    key_id, key_value = result
    save_state(args.state, state)

    # 輸出 key_id\tkey_value
    print(f"{key_id}\t{key_value}")


if __name__ == "__main__":
    main()
