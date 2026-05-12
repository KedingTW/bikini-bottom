# 多 Agent 協作 — 結構性問題討論（會議紀錄）

> 起始日期：2026-04-22
> 背景：Phase 1 測試過程中發現的結構性問題
> 參考：`Sample.md`（社群開發者的 AGENTS.md prompt 範例，羅馬軍團主題）
> 討論狀態：進行中

---

## 討論順序（依相依性排列）

```
問題 2（協作順序）← 最底層，定義整個流程骨架
  ↓
問題 3（後端測試）← 順序裡的關鍵環節，沒有它整合就是假的
  ↓
問題 4（AI Code Review）← Review 放在流程的哪個位置
  ↓
問題 1（mention 斷鏈）← 流程確定後，才知道誰在什麼時候該通知誰
  ↓
問題 5（Sample.md 借鑑）← 最後用設計模式把以上固化到 steering
```

---

## 議題 A：協作順序（問題 2）

**狀態：🟡 討論中**

**現狀：**
- 前後端整合時流程不清楚
- 派大星 PR #1 還沒合併，海綿寶寶就開始串接
- 整合測試完全沒做 — 前後端從來沒有一起跑過

**Kiro 提案的流程：**
```
1. 後端開發 → push 到分支（不開 PR）
2. 後端自測（跑起來，curl 測 API）
3. 通知前端：API 就緒，附上規格
4. 前端串接 → push 到分支
5. 整合測試（前後端一起跑，驗證能通）
6. 各自開 PR → AI Code Review
7. 通知人類：前後端都準備好 review
```

**關鍵差異（vs 目前做法）：**
- Code Review 放在整合測試之後，不是之前
- 後端要先自測通過才通知前端
- 整合測試通過後才進 review 流程

**結論：✅ 已確認**

流程順序：
```
1. 後端開發 → push 到分支（不開 PR）
2. 後端自測（容器裡跑起 API，curl 測 I/O）
3. 通知前端：API 就緒，附上規格
4. 前端串接 → push 到分支
5. 整合測試（派大星跑 API，用 curl 驗證前端 fetch 的 URL/method/body 與 API 實際行為一致）
6. 各自開 PR → AI Code Review
7. AI Code Review 修正（如有）→ 如有程式碼修改，重新整合測試
8. 通知人類：前後端都準備好 review
9. 人類 review（如有問題 → 修改 → 回到步驟 7）
10. 人類合併 PR
11. 人類部署 develop 到測試環境，自行測試
```

補充規則：
- PR 合併一定是最後一步，由人類執行
- 比奇堡團隊的環境只算「開發環境」，不是測試環境
- 人類 review 在 AI Code Review 全部完成後才進行
- 整合測試 = 確認 API I/O 正確，不需要瀏覽器模擬

---

## 議題 B：後端測試（問題 3）

**狀態：✅ 已確認**

**現狀：**
- API Server 沒有真正運作，前端串接是盲猜
- 派大星寫的 API 只有程式碼，沒有跑起來驗證過

**結論：**
- 方案 A：Dockerfile 按角色訂製
- 通用 Dockerfile 維持現狀（OpenAB + git + gh）
- 派大星用 `Dockerfile.patrick`，額外安裝 Python + pip（跑 FastAPI/uvicorn）
- docker-compose.yml 裡 patrick 改用 `Dockerfile.patrick`
- 派大星開發完後在容器裡 `uvicorn app.main:app` 跑起來，用 curl 自測 API I/O
- 海綿寶寶不需要額外 runtime（前端是靜態 HTML）
- 未來其他角色有特殊需求也用同樣模式：`Dockerfile.<角色>`

---

## 議題 C：AI Code Review 機制（問題 4）

**狀態：✅ 已確認**

**結論：**
- 泡芙阿姨升級為真正的 OpenAB agent（Phase 1）
- Phase 1：人類手動 mention 泡芙阿姨去 review（先驗證 review 品質）
- Phase 2：章魚哥上線後接管指揮泡芙阿姨（PM 管流程）
- Phase 3：蟹老闆上線管商業決策
- 不再依賴 GitHub CI 的 AI Code Review（或作為輔助，不是主要機制）
- 一口氣解決三個問題：時序問題（人類/PM 控制時機）、重複意見（agent 有 context）、review 品質（agent 能互動）

**泡芙阿姨作為 agent 的職責：**
- 收到 mention 後去看指定 PR
- 用 `gh pr review` 留 review 意見
- 能看到工程師前幾輪的回覆，不重複提已決定不修的項目
- 完成後向上呈報（Phase 1 呈報人類，Phase 2 呈報章魚哥）

**向上呈報機制（所有角色通用）：**
- Phase 1：所有角色完成任務後 mention 人類（米哥）
- Phase 2：工程師 + 泡芙阿姨 → mention 章魚哥；章魚哥 → mention 人類
- Phase 3：工程師 + 泡芙阿姨 → 章魚哥 → 蟹老闆 → 人類

**額外決定：**
- 第 3 輪 push 觸發第 4 輪的問題 → 泡芙阿姨升級後不再依賴 CI 標籤觸發，問題自然消失
- 重複意見問題 → agent 有 context，自然解決

---

## 議題 D：mention 斷鏈（問題 1）

**狀態：⚪ 等待議題 A-C 結論**

**現狀：**
- agent 經常忘記 mention 對方
- 人類需要不斷提醒

**依賴議題 A-C：** 流程確定後，才知道誰在什麼時候該通知誰。

**Sample.md 的做法：**
- COMPLETION_PROTOCOL — 每次回應最後一行強制 mention 指揮官

**結論：**
> 待前面議題確認後討論

---

## 議題 E：Sample.md 設計模式借鑑（問題 5）

**狀態：⚪ 等待議題 A-D 結論**

**值得借鑑的模式：**
1. COMPLETION_PROTOCOL — 強制 mention
2. WORKFLOW_POSITION — 流程位置定義
3. OUT_OF_SCOPE — 職責邊界
4. RECOMMENDED_MODEL — 角色用不同模型
5. BOT_TO_BOT — trusted_bot_ids

**依賴議題 A-D：** 所有流程和機制確定後，才能決定怎麼固化到 steering。

**結論：**
> 待前面議題確認後討論

---

## 對話紀錄分析（2026-04-21 下午 3:00-3:12）

### 正面觀察
- 派大星和海綿寶寶成功互相 mention 並完成 API 規格對齊
- 海綿寶寶主動問了 CORS 問題，派大星立刻修好並 push
- 前後端對接從溝通到 PR 完成只花了約 10 分鐘
- AI Code Review 3 輪流程順暢，海綿寶寶判斷修/不修的理由合理
- 泡芙阿姨通知正常運作

### 問題觀察
1. 第 3 輪 push 又觸發了第 4 輪 AI Code Review（標籤切換時序）
2. 前端串接是盲猜（API Server 沒有跑起來）
3. 協作順序問題（PR 沒合併就開始串接，沒有整合測試）
4. AI Code Review 3 輪大量重複意見
5. mention 協作基本成功但仍需提醒
