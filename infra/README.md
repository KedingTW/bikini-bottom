# 🏝️ 比奇堡 ECS Fargate Spot 部署

基於 [OpenAB 官方參考架構](https://github.com/openabdev/openab/blob/main/docs/refarch/aws-ecs-fargate-spot.md)。

## 架構

- **Region**: us-east-1（最便宜、Spot 容量最充足）
- **VPC**: 全 public subnet，無 NAT Gateway
- **計算**: ECS Fargate Spot，每角色獨立 Task
- **映像**: ECR（自建映像 = openab + git + gh CLI）
- **Secret**: SSM Parameter Store Standard（免費）
- **Config**: GitHub Gist URL（OpenAB 原生支援）
- **Auth 持久化**: S3 bucket + init/sidecar containers

## 角色

| 角色 | 規格 | 用途 |
|------|------|------|
| bob (海綿寶寶) | 0.25 vCPU / 512 MB | 開發 |
| patrick (派大星) | 0.25 vCPU / 512 MB | 開發 |
| puff (泡芙老師) | 0.25 vCPU / 512 MB | Code Review |
| gary (小蝸) | 0.25 vCPU / 512 MB | slash-bot |

## 部署

```bash
# 一鍵部署
./infra/deploy.sh

# 單獨部署某角色
./infra/deploy.sh bob
```

## 調整規格 SOP

見 [docs/fargate-scaling-sop.md](../docs/fargate-scaling-sop.md)
