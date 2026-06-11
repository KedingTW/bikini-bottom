# 神奇海螺升級 — 任務

## Phase 1：小蝸接收容器管理指令

- [ ] 2. 指令改名（`/conch-*` → `/status`, `/heal`, `/logs`, `/archive`）
- [ ] 5. 測試小蝸的新指令能正常運作

## Phase 2：建立神奇海螺 OpenAB Agent

- [ ] 6. 在 NAS 建立 `agents/conch/projects` 目錄
- [ ] 7. 建立 `agents/conch/` 目錄結構（config.toml、steering、.gitconfig、gh hosts、.openab）
- [ ] 8. 撰寫 personality.md（神秘、簡短、果斷風格）
- [ ] 9. 撰寫 workflow.md（求助回答、流程導航、不寫程式碼）
- [ ] 10. 更新 `docker-compose.yml`：移除 magic-conch service，新增 conch service
- [ ] 11. 啟動容器，驗證 `docker logs conch` 顯示 connected

## Phase 3：文件和整合更新

- [ ] 12. 更新 `shared/steering/team-members.md`（海螺角色描述）
- [ ] 13. 更新 `README.md`（角色表、架構圖）
- [ ] 14. 更新 `docs/bot-setup-sop.md`（容器對應表）
- [ ] 15. 更新其他 agent 的 workflow（加入「問海螺」的選項）
- [ ] 16. 刪除或標記 `services/magic-conch/` 為 deprecated
- [ ] 17. Commit & push
