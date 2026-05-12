# 🏝️ 比奇堡 ECS Fargate Spot 部署方案

> 基於 [OpenAB 官方參考架構](https://github.com/openabdev/openab/blob/main/docs/refarch/aws-ecs-fargate-spot.md)

## 架構總覽

| 項目 | 選擇 | 理由 |
|------|------|------|
| Region | us-east-1 | 最便宜、Spot 容量最充足 |
| 配置方式 | AWS CLI 腳本 | 官方建議，資源少不需 IaC 框架 |
| VPC | 全 public subnet，無 NAT | 省 $32+/月 |
| 計算 | Fargate Spot 0.25vCPU/512MB | ~$2.7/agent/月 |
| 映像 | ECR（自建 = openab + git + gh） | 需要 git/gh CLI |
| Secret | SSM Parameter Store Standard | 免費 |
| Config | GitHub Gist URL | OpenAB 原生支援 |
| Auth 持久化 | S3 + init/sidecar | Spot 中斷不丟 token |

## 成本估算

| 項目 | 數量 | 月費 |
|------|------|------|
| Fargate Spot (bob) | 0.25vCPU/512MB | ~$2.7 |
| Fargate Spot (patrick) | 0.25vCPU/512MB | ~$2.7 |
| Fargate Spot (puff) | 0.25vCPU/512MB | ~$2.7 |
| Fargate Spot (gary/slash-bot) | 0.25vCPU/512MB | ~$2.7 |
| Public IPv4 × 4 | $0.005/hr each | ~$14.4 |
| S3 (auth state) | < 1MB | ~$0 |
| CloudWatch Logs | 3 天保留 | ~$0.2 |
| SSM Parameter Store | ~15 params | $0 |
| ECR | 2 images | ~$0.1 |
| **合計** | | **~$25.5/月** |

> Public IPv4 是最大的額外成本。如果未來改用 IPv6-only subnet 可省 $14.4/月，降到 ~$11/月。

## 部署流程

```
1. setup-ssm-params.sh   → 寫入所有 secrets 到 SSM
2. deploy.sh vpc         → 建立 VPC + subnet + SG
3. deploy.sh ecr         → 建立 ECR + build & push images
4. deploy.sh iam         → 建立 IAM roles
5. deploy.sh infra       → 建立 S3 + CloudWatch + ECS Cluster
6. deploy.sh bob         → 部署 bob
7. deploy.sh patrick     → 部署 patrick
8. deploy.sh puff        → 部署 puff
9. deploy.sh gary        → 部署 gary (slash-bot)
10. login-agent.sh bob   → 首次 kiro-cli 認證
11. login-agent.sh patrick
12. login-agent.sh puff
```

或一鍵：`./infra/deploy.sh all`

## 檔案結構

```
infra/
├── README.md              # 說明
├── deploy.sh              # 主部署腳本
├── setup-ssm-params.sh    # SSM 參數初始化
├── login-agent.sh         # Agent 首次認證
├── scale-agent.sh         # 規格調整
└── .env.infra             # (自動產生) VPC/subnet IDs

docs/
├── openab-fargate-spot-deployment.md  # 本文件
└── fargate-scaling-sop.md             # 規格調整 SOP
```

## 前置準備

1. **AWS CLI** 已安裝且有足夠權限
2. **Docker** 已安裝（build image 用）
3. **Discord Bot Tokens** × 4（bob, patrick, puff, gary）
4. **GitHub PAT** (`GH_TOKEN`)
5. 每個 OAB agent 的 **config.toml** 放到 GitHub Gist

## Config Gist 範例

每個角色建立一個 secret gist，內容如 `agents/<name>/config.toml`，但把 channel ID 改用 `${ENV_VAR}`：

```toml
# bob 的 config.toml gist
[discord]
bot_token = "${DISCORD_BOT_TOKEN}"
allowed_channels = ["${CHANNEL_GENERAL}", "${KIRO_USAGE_CHANNEL_ID}"]
allow_bot_messages = "mentions"
allow_user_messages = "multibot-mentions"

[agent]
command = "kiro-cli"
args = ["acp", "--trust-all-tools"]
working_dir = "/home/agent/projects"
inherit_env = ["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]

[pool]
max_sessions = 3
session_ttl_hours = 1

[reactions]
enabled = true
remove_after_reply = false
```

> 注意：Fargate 上 `session_ttl_hours` 建議設短（1h），因為 512MB 記憶體有限。

## 規格調整

見 [fargate-scaling-sop.md](./fargate-scaling-sop.md)

```bash
# 例：bob OOM 了，升到 1GB
./infra/scale-agent.sh bob 256 1024
```
