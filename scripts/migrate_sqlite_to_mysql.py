#!/usr/bin/env python3
"""SQLite → MySQL 資料遷移腳本"""
import sqlite3
import subprocess
import time
import sys

# MySQL 連線資訊
MYSQL_HOST = "admin-mysql"
MYSQL_PORT = 3306
MYSQL_USER = "admin"
MYSQL_PASSWORD = "5dukJm7ocqXEHKs92EhyS3dw"
MYSQL_DATABASE = "admin_dashboard"
SQLITE_DB = "services/admin/data/metrics.db"

# 透過 kubectl port-forward 連 MySQL
# 或直接用 kubectl exec 在 pod 裡執行

def run_mysql_cmd(sql, database=MYSQL_DATABASE):
    """透過 kubectl exec 在 MySQL pod 執行 SQL"""
    cmd = [
        "kubectl", "exec", "-n", "bikini-bottom",
        "deployment/admin-mysql", "--",
        "mysql", f"-u{MYSQL_USER}", f"-p{MYSQL_PASSWORD}", database,
        "-e", sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    return True

def run_mysql_cmd_stdin(sql, database=MYSQL_DATABASE):
    """透過 stdin 送大量 SQL"""
    cmd = [
        "kubectl", "exec", "-i", "-n", "bikini-bottom",
        "deployment/admin-mysql", "--",
        "mysql", f"-u{MYSQL_USER}", f"-p{MYSQL_PASSWORD}", database
    ]
    result = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[:500]}")
        return False
    return True

print("=== 開始 SQLite → MySQL 遷移 ===")

# 1. 建立表結構
print("\n[1/4] 建立 MySQL 表結構...")
create_tables = """
CREATE TABLE IF NOT EXISTS metrics_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts VARCHAR(64) NOT NULL,
    agent VARCHAR(128) NOT NULL,
    cpu_milli DOUBLE NOT NULL,
    memory_mb DOUBLE NOT NULL,
    INDEX idx_ts (ts),
    INDEX idx_agent (agent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts VARCHAR(64) NOT NULL,
    agent VARCHAR(128) NOT NULL,
    level VARCHAR(32) NOT NULL,
    message TEXT NOT NULL,
    dismissed INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    department VARCHAR(256),
    password_hash VARCHAR(512) NOT NULL,
    role VARCHAR(64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cache (
    `key` VARCHAR(256) PRIMARY KEY,
    data LONGTEXT,
    ts VARCHAR(64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS deploy_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts VARCHAR(64) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    user_name VARCHAR(256) NOT NULL,
    agent VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL,
    status VARCHAR(64) NOT NULL,
    message TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS push_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts VARCHAR(64) NOT NULL,
    user_name VARCHAR(256) NOT NULL,
    platform VARCHAR(64) NOT NULL,
    target VARCHAR(256) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(64),
    scheduled_at VARCHAR(64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS mcp_registry (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(128) NOT NULL,
    name VARCHAR(256) NOT NULL,
    url VARCHAR(1024) NOT NULL,
    headers TEXT,
    available_tools TEXT,
    tags VARCHAR(512),
    disabled INT DEFAULT 0,
    created_at VARCHAR(64) NOT NULL,
    updated_at VARCHAR(64) NOT NULL,
    token VARCHAR(512),
    UNIQUE KEY uk_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS mcp_assignments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(128) NOT NULL,
    mcp_key VARCHAR(128) NOT NULL,
    enabled INT DEFAULT 1,
    allowed_tools TEXT,
    is_draft INT DEFAULT 0,
    UNIQUE KEY uk_agent_mcp (agent_name, mcp_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS skill_assignments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(128) NOT NULL,
    skill_name VARCHAR(128) NOT NULL,
    enabled INT DEFAULT 1,
    is_draft INT DEFAULT 0,
    UNIQUE KEY uk_agent_skill (agent_name, skill_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

if not run_mysql_cmd_stdin(create_tables):
    print("FATAL: 建表失敗")
    sys.exit(1)
print("  ✓ 表結構建立完成")

# 2. 遷移資料
print("\n[2/4] 開始遷移資料...")
conn = sqlite3.connect(SQLITE_DB)
cursor = conn.cursor()

# 小表先遷移
small_tables = [
    ("users", ["id", "name", "department", "password_hash", "role"]),
    ("cache", ["key", "data", "ts"]),
    ("alerts", ["id", "ts", "agent", "level", "message", "dismissed"]),
    ("deploy_history", ["id", "ts", "user_id", "user_name", "agent", "action", "status", "message"]),
    ("push_history", ["id", "ts", "user_name", "platform", "target", "content", "status", "scheduled_at"]),
    ("mcp_registry", ["id", "key", "name", "url", "headers", "available_tools", "tags", "disabled", "created_at", "updated_at"]),
    ("mcp_assignments", ["id", "agent_name", "mcp_key", "enabled", "allowed_tools", "is_draft"]),
    ("skill_assignments", ["id", "agent_name", "skill_name", "enabled", "is_draft"]),
]

for table, cols in small_tables:
    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
    count = cursor.fetchone()[0]
    if count == 0:
        print(f"  {table}: 0 rows (skip)")
        continue

    cursor.execute(f"SELECT * FROM [{table}]")
    rows = cursor.fetchall()

    # 構建 INSERT 語句
    col_names = ", ".join(f"`{c}`" for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    
    # 批次生成 SQL
    batch_sql = f"INSERT IGNORE INTO `{table}` ({col_names}) VALUES\n"
    value_strs = []
    for row in rows:
        escaped = []
        for val in row:
            if val is None:
                escaped.append("NULL")
            elif isinstance(val, (int, float)):
                escaped.append(str(val))
            else:
                # 轉義引號
                val_str = str(val).replace("\\", "\\\\").replace("'", "\\'")
                escaped.append(f"'{val_str}'")
        value_strs.append(f"({', '.join(escaped)})")
    
    # 每 500 筆一批
    batch_size = 500
    for i in range(0, len(value_strs), batch_size):
        batch = value_strs[i:i+batch_size]
        sql = f"INSERT IGNORE INTO `{table}` ({col_names}) VALUES\n" + ",\n".join(batch) + ";"
        if not run_mysql_cmd_stdin(sql):
            print(f"  ✗ {table}: batch {i} failed")
            break
    
    print(f"  ✓ {table}: {count} rows")

# 3. 遷移 metrics_history（大表，分批）
print("\n[3/4] 遷移 metrics_history（大表）...")
cursor.execute("SELECT COUNT(*) FROM metrics_history")
total = cursor.fetchone()[0]
print(f"  總計 {total} 行，分批遷移中...")

batch_size = 5000
offset = 0
migrated = 0

while offset < total:
    cursor.execute(f"SELECT id, ts, agent, cpu_milli, memory_mb FROM metrics_history LIMIT {batch_size} OFFSET {offset}")
    rows = cursor.fetchall()
    if not rows:
        break
    
    value_strs = []
    for row in rows:
        id_, ts, agent, cpu, mem = row
        ts_e = str(ts).replace("'", "\\'")
        agent_e = str(agent).replace("'", "\\'")
        value_strs.append(f"({id_}, '{ts_e}', '{agent_e}', {cpu}, {mem})")
    
    sql = "INSERT IGNORE INTO metrics_history (id, ts, agent, cpu_milli, memory_mb) VALUES\n" + ",\n".join(value_strs) + ";"
    if not run_mysql_cmd_stdin(sql):
        print(f"  ✗ 批次 {offset} 失敗")
        break
    
    offset += batch_size
    migrated += len(rows)
    if migrated % 50000 == 0:
        print(f"  ... {migrated}/{total} ({migrated*100//total}%)")

print(f"  ✓ metrics_history: {migrated} rows migrated")

# 4. 驗證
print("\n[4/4] 驗證行數...")
verify_sql = """
SELECT 'metrics_history' as tbl, COUNT(*) as cnt FROM metrics_history
UNION ALL SELECT 'alerts', COUNT(*) FROM alerts
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'mcp_registry', COUNT(*) FROM mcp_registry
UNION ALL SELECT 'mcp_assignments', COUNT(*) FROM mcp_assignments
UNION ALL SELECT 'skill_assignments', COUNT(*) FROM skill_assignments;
"""
cmd = [
    "kubectl", "exec", "-n", "bikini-bottom",
    "deployment/admin-mysql", "--",
    "mysql", f"-u{MYSQL_USER}", f"-p{MYSQL_PASSWORD}", MYSQL_DATABASE,
    "-e", verify_sql
]
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)

conn.close()
print("\n=== 遷移完成 ===")
