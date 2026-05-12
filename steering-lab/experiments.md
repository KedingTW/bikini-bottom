# 🧪 實驗紀錄

> 每次 steering 實驗都記錄在這裡，方便回溯和對齊。
> 格式：實驗編號、角色、組合、目的、結果、結論。

---

## EXP-001 — 海綿寶寶 Redmine 自動任務處理

- **日期**：2026-04-16
- **角色**：bob
- **組合**：`exp-redmine`
- **面向變更**：
  - `workflow`: v1-worklog → exp-redmine-auto（新增 Redmine 自動讀取 + 處理 + 回報流程）
  - `mcp-tools`: v1-redmine → v2-redmine（改用 redmine-mcp-server 的專用工具）
  - `personality`: v1-base（不變）
- **目的**：驗證海綿寶寶能否透過 MCP 自動讀取 Redmine issue、執行任務、回覆留言、更新狀態
- **測試方式**：在 Discord 跟海綿寶寶說「去看你的 Redmine 任務」
- **結果**：✅ 基本流程跑通，海綿寶寶成功讀取 issue #1221 並回覆留言
- **待改善**：
  - 接收到 issue 編號後的處理順序仍需調教（步驟執行順序、留言格式等）
  - Redmine 工作流程（狀態轉換規則）尚未明訂，需請開發主管提供團隊 SOP
  - 需要觀察更多實際對話紀錄來迭代 workflow steering
- **下一步**：收集海綿寶寶的 Discord 對話紀錄，逐步調整 exp-redmine-auto.md


### 測試紀錄

#### 測試 1（2026-04-16 下午，加入 redmine-sop v1 後）
- **指令**：「處理 issue 1221」
- **正面**：
  - 有先讀 WORKLOG.md（遵守交接原則）
  - 狀態更新順序正確：尚未開發 → 開發中 → review
  - 知道不能自行改為「已完成」
  - 最後有更新 WORKLOG.md
- **問題**：
  - 遇到 500 錯誤後瘋狂重試 update 10 次，浪費 token → 已加入錯誤處理規則（最多重試 2 次）
  - 留言中的 markdown/emoji 導致 500 → 已加入「留言使用純文字」規則
  - 數學題不需要走 review 狀態 → 已加入狀態判斷邏輯（非程式碼任務不走 review）
  - 沒有先釐清需求就直接開始 → 數學題太明確所以影響不大，但流程上應先確認
- **SOP 調整**：新增第七節（錯誤處理）、第八節（狀態判斷邏輯）、修改第五節（留言純文字）

---

## EXP-002 — 海綿寶寶 Git Flow 整合

- **日期**：2026-04-16
- **角色**：bob
- **組合**：`exp-git-flow`
- **面向變更**：
  - `workflow`: exp-redmine-auto → exp-git-flow（整合 git flow 步驟到任務處理流程）
  - `git-flow`: 新增 shared/git-flow/v1-standard.md（Git Flow 作業規範）
  - `mcp-tools`: v2-redmine（不變）
  - `redmine-sop`: v1-standard（不變）
  - `personality`: v1-base（不變）
- **目的**：驗證海綿寶寶能否在處理涉及程式碼的 Redmine 任務時，自動走 Git Flow（開分支 → 開發 → push → 開 PR → 回報 Redmine）
- **前置條件**：
  - Dockerfile 需加入 `gh`（GitHub CLI）
  - Agent 容器需執行 `gh auth login`
- **測試方式**：在 Discord 指派一個涉及程式碼修改的 Redmine issue，觀察海綿寶寶是否正確走 Git Flow
- **結果**：⬜ 待測試
- **待改善**：⬜ 待測試後記錄
