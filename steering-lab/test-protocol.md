# 🧪 Steering 測試協議

## 測試模式：Kiro IDE + Discord 人工轉貼

### 角色分工
- **Kiro IDE（你）**：建立測試 issue、分析對話紀錄、調整 steering、重啟容器
- **人類（我）**：在 Discord 上觸發 Agent、將 Agent 回覆轉貼到 Kiro IDE、提供反饋

### 測試流程

1. **準備**
   - Kiro 在 Redmine 建立測試 issue（指派給目標角色）
   - Kiro 確認 steering 已更新並重啟容器

2. **執行**
   - 人類在 Discord 跟角色說「處理 issue #XXXX」
   - 角色執行任務

3. **回報**
   - 人類將角色的 Discord 回覆（含工具呼叫紀錄）轉貼到 Kiro IDE
   - 格式：直接貼文字，包含工具呼叫列表和角色的回覆內容

4. **檢討**
   - Kiro 分析角色行為：哪些符合預期、哪些有問題
   - 討論需要調整的 steering 內容
   - Kiro 修改 steering 並重啟容器

5. **迭代**
   - 重複步驟 1-4，直到行為符合預期
   - 每次迭代記錄在 `steering-lab/experiments.md`

### 適用場景
- Redmine 任務處理流程調教
- Git Flow 工作流程調教
- 新 SOP 導入測試
- 任何需要觀察角色行為並迭代優化的場景

### 注意事項
- 每次測試前確認容器已重啟（steering 變更需要重啟才生效）
- 轉貼時盡量包含完整的工具呼叫紀錄，不只是最終回覆
- 測試 issue 建在「Agent測試專案」（project_id: 9）
