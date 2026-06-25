# Agent 角色登錄表與維護規範

## 所有 Bot UID 對照表

新增或修改角色時，以此表為唯一真相來源（Single Source of Truth）。

| Agent 別名 | 角色名 | Discord Bot UID |
|-----------|--------|-----------------|
| bob | 海綿寶寶 | 1492085509596516362 |
| patrick | 派大星 | 1496023645083009024 |
| pearl | 珍珍 | 1509104920954142871 |
| larry | 蝦霸 | 1509105546060501184 |
| gary | 小蝸 | 1493800835853975562 |
| conch | 神奇海螺 | 1505753410765459567 |
| puff | 泡芙老師 | 1503574146117013555 |
| squidward | 章魚哥 | 1503698574477627482 |
| sandy | 珊迪 | 1504275756488986774 |
| mermaid-man | 海超人 | 1511295414366769202 |

## 新增角色時必做事項

### 1. 更新所有現有 agent 的 `trusted_bot_ids`

每個 agent 的 `agents/bikini-bottom/<alias>/config.toml` 中的 `trusted_bot_ids` 必須包含**除了自己以外的所有其他 bot UID**。

新增一個角色時，必須：
- 在新角色的 `config.toml` 中列出所有其他 bot 的 UID
- 在所有既有角色的 `config.toml` 中加入新角色的 UID

**範例腳本（用 python3 執行）：**

```python
import os, re

base = "agents/bikini-bottom"
# 從上方表格取得完整 bot 清單
bots = {
    "bob": "1492085509596516362",
    "patrick": "1496023645083009024",
    # ... 所有 bot
}

for agent, own_uid in bots.items():
    config_path = os.path.join(base, agent, "config.toml")
    with open(config_path, 'rb') as f:
        content = f.read()
    
    match = re.search(rb'trusted_bot_ids\s*=\s*\[.*?\]', content)
    if not match:
        continue
    
    old_line = match.group(0)
    existing_ids = set(re.findall(rb'"(\d+)"', old_line))
    expected = set(uid.encode() for name, uid in bots.items() if name != agent)
    missing = expected - existing_ids
    
    if not missing:
        continue
    
    existing_list = re.findall(rb'"(\d+)"', old_line)
    for m in sorted(missing):
        existing_list.append(m)
    
    new_ids_str = b', '.join(b'"' + uid + b'"' for uid in existing_list)
    new_line = b'trusted_bot_ids = [' + new_ids_str + b']'
    new_content = content.replace(old_line, new_line)
    
    with open(config_path, 'wb') as f:
        f.write(new_content)
```

### 2. 更新共用 steering `shared/steering/team-members.md`

在成員表格中加入新角色的列，包含：
- emoji + 中文名 + 英文別名
- 職責描述
- Discord UID
- Mention 寫法 `<@UID>`

### 3. 更新此文件

在上方的 UID 對照表中加入新角色。

### 4. 重啟所有 agent

```bash
kubectl rollout restart deployment <所有agent名稱> -n bikini-bottom
```

## 重要注意事項

### config.toml 修改規則

- **絕對不要用 python 的一般 write mode 重寫整個 config.toml** — 會破壞原始的換行符號和格式
- 正確做法：用 binary mode (`'rb'`/`'wb'`) 讀寫，只替換目標行
- 或用 `sed -i` 做單行替換
- **不要動 `allowed_role_ids`** — 每個 agent 的 role ID 是各自的 Discord role，不是統一的

### team-members.md 編碼

- 必須保持 UTF-8 編碼
- 使用 `file` 指令確認：應顯示 `Unicode text, UTF-8 text`
- 如果顯示 `Non-ISO extended-ASCII` 表示已損壞，需要重寫

### UID 取得方式

如果只有 bot token，可以用 base64 解碼 token 第一段取得 UID：

```bash
echo "<token第一段>=" | base64 -d
```

Token 格式為 `<base64_uid>.<timestamp>.<hmac>`，第一段 base64 解碼就是 bot user ID。
