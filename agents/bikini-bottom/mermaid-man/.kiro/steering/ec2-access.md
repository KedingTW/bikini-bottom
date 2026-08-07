---
inclusion: auto
---
# EC2 連線紀錄

## 連線方式

使用 Python paramiko（容器內沒有原生 ssh binary）：

```python
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('18.183.94.59', username='ubuntu', key_filename='/home/agent/.ssh/EC-Middle.pem', timeout=15)
stdin, stdout, stderr = ssh.exec_command('<command>')
print(stdout.read().decode().strip())
ssh.close()
```

## EC2 清單

### EC-Middle（唯一主機）

| 項目 | 值 |
|------|-----|
| Public IP | 18.183.94.59 |
| Private IP | 10.42.0.251 |
| SSH User | ubuntu |
| SSH Key | /home/agent/.ssh/EC-Middle.pem |
| SSH Port 22 | 已開放 |
| OS | Ubuntu 26.04 LTS |
| 上面跑的服務 | mcp-server、mgt-admin（docker-compose）、bikini-bottom K3s |
| NAS Mount | /mnt/nas-kd-share |

## 主機上的服務

### Docker Compose 服務

| Container | 用途 | Port |
|-----------|------|------|
| mcp-server | MCP Server（Laravel） | 1601:80, 1602:443 |
| mcp-redis | MCP 用 Redis | 1603:6379 |
| mcp-mysql | MCP 用 MySQL 8.0 | 1604:3306 |
| mgt-admin-phpmyadmin | phpMyAdmin | 8080:80 |
| mgt-admin-api | 管理後台 API | 8000 |
| mgt-admin-redis | 管理後台 Redis | 6379 |
| mgt-admin-mysql | 管理後台 MySQL | 3306 |

### K3s 服務

- bikini-bottom namespace: admin, admin-mysql, admin-nginx, admin-phpmyadmin, kenny
- mgt-admin namespace: api, frontend（dev + prod）

## MCP Server 部署資訊

| 項目 | 值 |
|------|-----|
| Repo | KedingTW/mcp-server |
| 部署路徑 | /opt/deploy/mcp-server/ |
| 部署方式 | Docker Compose（volume mount，code 更新不需 rebuild） |
| 部署腳本 | /opt/deploy/mcp-server/deploy.sh |

### 部署指令

```bash
# 部署指定 branch（一般 code 更新，零 downtime）
cd /opt/deploy/mcp-server && sudo bash deploy.sh <branch>

# rebuild image（dockerfile/docker-compose 變更時）
cd /opt/deploy/mcp-server && sudo bash deploy.sh <branch> --build

# 只重啟容器
cd /opt/deploy/mcp-server && sudo bash deploy.sh --restart

# 只更新 .env
cd /opt/deploy/mcp-server && sudo bash deploy.sh --env-only
```

## 注意事項

- 容器內沒有原生 ssh，用 paramiko（已安裝）
- 出口 IP：118.163.109.105
- EC-Middle.pem 在 /home/agent/.ssh/EC-Middle.pem
