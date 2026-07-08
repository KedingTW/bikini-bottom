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
ssh.connect('<IP>', username='ubuntu', key_filename='/home/agent/.ssh/EC-Middle.pem', timeout=15)
stdin, stdout, stderr = ssh.exec_command('<command>')
print(stdout.read().decode().strip())
ssh.close()
```

## EC2 清單

### 比奇堡 + 電商（EC-Middle）

| 項目 | 值 |
|------|-----|
| Public IP | 13.193.102.165 |
| Private IP | 10.42.0.251 |
| SSH User | ubuntu |
| SSH Key | /home/agent/.ssh/EC-Middle.pem |
| SSH Port 22 | any（已開放） |
| 上面跑的服務 | mgt-admin（docker-compose）、bikini-bottom K3s |
| NAS Mount | /mnt/kd-dev |

### Agent 平台測試站

| 項目 | 值 |
|------|-----|
| Public IP | 13.112.76.16 |
| Private IP | 10.42.0.246 |
| SSH User | ubuntu |
| SSH Key | 待確認（EC-Middle.pem 或 BikiniBottom.pem） |
| SSH Port 22 | 未對我開放（timeout） |
| 上面跑的服務 | ai-chatbox、ai-agent-api、mcp-server、MySQL |
| 網址 | http://13.112.76.16/agent/ |

## 注意事項

- 容器內沒有原生 ssh，用 paramiko（已安裝）
- 出口 IP：118.163.109.105
- EC-Middle.pem 在 /home/agent/.ssh/EC-Middle.pem
- NAS 上備份位置：/mnt/kd-dev/shared/workspace/e-commerce/ec2/EC-Middle.pem
