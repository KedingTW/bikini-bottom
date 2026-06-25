#!/usr/bin/env python3
"""
從 order-transform 的 Discord threads 中提取被標記 💯 的 Q&A 對。
輸出格式與 exam_text_tagged.jsonl 相同。
"""

import json
import time
import urllib.request
import sys
import re

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
BOT_NAME = "下單小幫手"
THREAD_MAP_PATH = "/home/kdprogramer/Projects/bikini-bottom/agents/keding-dc/order-transform/.openab/thread_map.json"
OUTPUT_PATH = "/mnt/kd-share/shared/workspace/order-transform-exam/questions/exam_from_discord.jsonl"

HEADERS = {"Authorization": f"Bot {BOT_TOKEN}", "User-Agent": "DiscordBot (https://keding.com, 1.0)"}


def fetch_messages(channel_id, before=None, limit=100):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={limit}"
    if before:
        url += f"&before={before}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.HTTPError as e:
        print(f"  Error fetching {channel_id}: HTTP {e.code} - {e.read().decode()}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  Error fetching {channel_id}: {e}", file=sys.stderr)
        return []


def get_all_messages(channel_id):
    """Fetch all messages from a thread (paginated)."""
    all_msgs = []
    before = None
    while True:
        msgs = fetch_messages(channel_id, before=before)
        if not msgs:
            break
        all_msgs.extend(msgs)
        if len(msgs) < 100:
            break
        before = msgs[-1]["id"]
        time.sleep(0.5)  # rate limit
    return all_msgs


def extract_answer_from_content(content):
    """
    Parse bot response to extract 品號, 數量, 對花備註.
    Returns list of dicts.
    """
    # Extract 品號 block
    pin_match = re.search(r'品號[：:]\s*```\s*\n(.*?)```', content, re.DOTALL)
    if not pin_match:
        pin_match = re.search(r'品號[：:]\s*\n((?:[A-Z0-9].*\n?)+)', content)
    
    # Extract 數量 block
    qty_match = re.search(r'數量[：:]\s*```\s*\n(.*?)```', content, re.DOTALL)
    if not qty_match:
        qty_match = re.search(r'數量[：:]\s*\n((?:[\d.].*\n?)+)', content)
    
    # Extract 對花備註 block
    note_match = re.search(r'對花備註[：:]\s*```\s*\n(.*?)```', content, re.DOTALL)

    if not pin_match or not qty_match:
        return None

    pins = [p.strip() for p in pin_match.group(1).strip().split('\n') if p.strip()]
    qtys = [q.strip() for q in qty_match.group(1).strip().split('\n') if q.strip()]
    
    notes = []
    if note_match:
        notes = [n.strip() for n in note_match.group(1).strip().split('\n')]
    
    # Pad notes to match length
    while len(notes) < len(pins):
        notes.append("")

    results = []
    for i, pin in enumerate(pins):
        item = {"品號": pin, "數量": qtys[i] if i < len(qtys) else "1"}
        if i < len(notes) and notes[i]:
            item["對花備註"] = notes[i]
        results.append(item)
    
    return results


def main():
    with open(THREAD_MAP_PATH) as f:
        thread_map = json.load(f)
    
    thread_ids = [k.replace("discord:", "") for k in thread_map.keys()]
    
    all_qa = []
    uid_counter = 1
    
    for tid in thread_ids:
        print(f"Scanning thread {tid}...", file=sys.stderr)
        msgs = get_all_messages(tid)
        msgs.reverse()  # oldest first
        
        # Find messages with 💯 reaction from the bot
        for i, m in enumerate(msgs):
            if m["author"].get("username") == BOT_NAME or m["author"].get("global_name") == BOT_NAME:
                reactions = m.get("reactions", [])
                has_100 = any(r["emoji"].get("name") == "💯" for r in reactions)
                if not has_100:
                    continue
                
                # Parse the answer
                answer = extract_answer_from_content(m["content"])
                if not answer:
                    continue
                
                # Find the preceding human message (the question)
                question_msg = None
                for j in range(i - 1, -1, -1):
                    author = msgs[j]["author"]
                    if author.get("username") != BOT_NAME and author.get("global_name") != BOT_NAME:
                        # Skip empty or system messages
                        content = msgs[j].get("content", "").strip()
                        if content and not content.startswith("<@&"):
                            question_msg = msgs[j]
                            break
                
                if not question_msg:
                    continue
                
                question_text = question_msg["content"]
                # Remove mentions from question
                question_text = re.sub(r'<@[!&]?\d+>', '', question_text).strip()
                
                if not question_text:
                    continue
                
                qa = {
                    "uid": f"D{uid_counter:03d}",
                    "id": f"DC{uid_counter:03d}",
                    "type": "text",
                    "source": "discord_100",
                    "source_thread": tid,
                    "source_msg_id": m["id"],
                    "question": question_text,
                    "answer": answer,
                    "noise_tags": [],
                }
                all_qa.append(qa)
                uid_counter += 1
                print(f"  Found 💯 Q&A: {qa['uid']}", file=sys.stderr)
        
        time.sleep(1)  # rate limit between threads
    
    # Write output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for qa in all_qa:
            f.write(json.dumps(qa, ensure_ascii=False) + "\n")
    
    print(f"\nDone! Extracted {len(all_qa)} Q&A pairs → {OUTPUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
