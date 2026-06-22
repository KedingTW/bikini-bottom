<template>
  <AgentDetailLayout :agents="agents" :selected-agent="selectedAgent" :loading="loading" @select="onSelect" @back="selectedAgent = null">
    <div v-if="!selectedAgent" class="text-center py-20 text-white/50 hidden md:block">
      <div class="text-3xl mb-2">🤖</div>
      <div>請選擇角色查看配置</div>
    </div>

    <div v-if="selectedAgent">
      <h2 class="text-lg font-semibold mb-4">{{ selectedAgent.display }} 配置</h2>

      <div class="space-y-2">
        <!-- 1. 基本配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('basic')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.basic ? '▼' : '▶' }}</span>
            <span class="font-medium">⚙️ 基本配置</span>
          </button>
          <div v-if="open.basic" class="px-4 pb-4 border-t border-white/5 space-y-4">
            <!-- Discord -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">Discord</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <Field label="Bot 訊息觸發" tip="是否接收其他 Bot 的訊息並處理">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.discord.allow_bot_messages" /><span class="text-sm text-white/70">{{ cfg.discord.allow_bot_messages ? '啟用' : '停用' }}</span></div>
                </Field>
                <Field label="使用者訊息觸發" tip="是否接收使用者的訊息並處理">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.discord.allow_user_messages" /><span class="text-sm text-white/70">{{ cfg.discord.allow_user_messages ? '啟用' : '停用' }}</span></div>
                </Field>
                <Field label="最大 Bot 對話輪數" tip="連續回覆 Bot 訊息的上限次數，避免無限迴圈">
                  <input v-model.number="cfg.discord.max_bot_turns" type="number" class="field-input">
                </Field>
                <Field label="訊息處理模式" tip="buffered=累積後批次處理、immediate=即時處理每則訊息">
                  <select v-model="cfg.discord.message_processing_mode" class="field-input"><option>buffered</option><option>immediate</option></select>
                </Field>
                <Field label="緩衝訊息數上限" tip="buffered 模式下，累積幾則訊息後觸發處理">
                  <input v-model.number="cfg.discord.max_buffered_messages" type="number" class="field-input">
                </Field>
                <Field label="批次 Token 上限" tip="單次批次處理的最大 token 數量">
                  <input v-model.number="cfg.discord.max_batch_tokens" type="number" class="field-input">
                </Field>
              </div>
              <div class="mt-4 space-y-3">
                <Field label="允許頻道" tip="只有這些頻道 ID 的訊息會被處理">
                  <TagInput v-model="cfg.discord.allowed_channels" />
                  <div class="flex flex-wrap gap-1 mt-1"><span v-for="ch in cfg.discord.allowed_channels" :key="ch" class="text-[10px] text-white/40">{{ channelMap[ch] || '' }}</span></div>
                </Field>
                <Field label="允許身分組" tip="只有這些身分組的訊息會被處理">
                  <TagInput v-model="cfg.discord.allowed_role_ids" />
                </Field>
                <Field label="信任 Bot ID" tip="這些 Bot 的訊息會被當作可信來源處理">
                  <TagInput v-model="cfg.discord.trusted_bot_ids" />
                  <div class="flex flex-wrap gap-1 mt-1"><span v-for="id in cfg.discord.trusted_bot_ids" :key="id" class="text-[10px] text-white/40">{{ botMap[id] || '' }}</span></div>
                </Field>
              </div>
            </fieldset>
            <!-- Agent -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">Agent</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="啟動指令" tip="Agent 的主要啟動程式"><input v-model="cfg.agent.command" class="field-input font-mono"></Field>
                <Field label="工作目錄" tip="Agent 的工作路徑">
                  <div class="flex gap-2">
                    <input v-model="cfg.agent.working_dir" class="field-input font-mono flex-1">
                    <button class="px-2 py-1 text-xs rounded bg-ocean-700 border border-white/15 text-white/60 hover:text-white shrink-0">📂</button>
                  </div>
                </Field>
              </div>
              <div class="mt-3 space-y-3">
                <Field label="啟動參數" tip="傳給 command 的參數列表"><TagInput v-model="cfg.agent.args" /></Field>
                <Field label="繼承環境變數" tip="從容器傳入 Agent 的環境變數名稱"><TagInput v-model="cfg.agent.inherit_env" /></Field>
              </div>
            </fieldset>
            <!-- Pool -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">Pool</legend>
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <Field label="最大 Session 數" tip="同時可執行的 Kiro session 上限"><input v-model.number="cfg.pool.max_sessions" type="number" class="field-input"></Field>
                <Field label="Session 存活時數" tip="Session 閒置幾小時後自動清除"><input v-model.number="cfg.pool.session_ttl_hours" type="number" class="field-input"></Field>
              </div>
            </fieldset>
            <!-- Reactions -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">Reactions</legend>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Field label="啟用反應" tip="是否在訊息上添加 emoji 反應表示處理狀態">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.reactions.enabled" /><span class="text-sm text-white/70">{{ cfg.reactions.enabled ? '啟用' : '停用' }}</span></div>
                </Field>
                <Field label="回覆後移除" tip="回覆完成後是否移除過程中的 emoji">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.reactions.remove_after_reply" /><span class="text-sm text-white/70">{{ cfg.reactions.remove_after_reply ? '是' : '否' }}</span></div>
                </Field>
                <Field label="工具顯示模式" tip="使用工具時的顯示方式">
                  <select v-model="cfg.reactions.tool_display" class="field-input"><option>emoji</option><option>text</option><option>none</option></select>
                </Field>
              </div>
              <div class="mt-4">
                <div class="text-sm text-white/60 mb-2">Emoji 設定</div>
                <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                  <Field v-for="(val, key) in cfg.reactions.emojis" :key="key" :label="emojiLabels[key] || key" :tip="'狀態：'+key">
                    <EmojiPicker v-model="cfg.reactions.emojis[key]" />
                  </Field>
                </div>
              </div>
            </fieldset>
            <!-- STT -->
            <fieldset class="border border-white/10 rounded-lg p-4 opacity-50 pointer-events-none relative">
              <legend class="text-sm text-white/40 px-1 font-medium">STT 語音轉文字</legend>
              <div class="absolute inset-0 flex items-center justify-center z-10">
                <span class="bg-ocean-800 px-3 py-1.5 rounded text-sm text-white/60 border border-white/10">🚧 目前尚未開放</span>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Field label="啟用"><Toggle :model-value="false" /></Field>
                <Field label="模型"><input value="whisper-large-v3" disabled class="field-input opacity-50"></Field>
                <Field label="API 位址"><input value="" disabled class="field-input opacity-50"></Field>
              </div>
            </fieldset>
            <!-- Cron 設定 -->
            <fieldset class="border border-white/10 rounded-lg p-4">
              <legend class="text-sm text-cyan-400 px-1 font-medium">排程設定</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="使用者排程" tip="是否啟用角色自訂的排程任務">
                  <div class="flex items-center gap-2"><Toggle v-model="cfg.cron.usercron_enabled" /><span class="text-sm text-white/70">{{ cfg.cron.usercron_enabled ? '啟用' : '停用' }}</span></div>
                </Field>
                <Field label="排程檔案路徑" tip="cronjob.toml 的檔案位置"><input v-model="cfg.cron.usercron_path" class="field-input font-mono"></Field>
              </div>
            </fieldset>
          </div>
        </div>

        <!-- 2. MCP 配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('mcp')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.mcp ? '▼' : '▶' }}</span>
            <span class="font-medium">🔌 MCP 配置</span>
            <span class="ml-auto text-sm text-white/40">{{ mcpEnabledCount }}/{{ mockMcp.length }}</span>
          </button>
          <div v-if="open.mcp" class="px-4 pb-4 border-t border-white/5 space-y-2">
            <div v-for="s in mockMcp" :key="s.name" class="bg-ocean-700/50 rounded-lg overflow-hidden">
              <div class="flex items-center gap-2 px-3 py-2.5 cursor-pointer hover:bg-white/5" @click="s._open = !s._open">
                <input type="checkbox" :checked="s.enabled" :indeterminate.prop="s.partial" @click.stop="toggleMcpServer(s)" class="w-4 h-4 accent-cyan-500">
                <span class="text-sm flex-1" :class="s.enabled ? 'text-cyan-300' : 'text-white/40'">{{ s.name }}</span>
                <span class="text-xs text-white/40">{{ s.enabledTools }}/{{ s.tools.length }}</span>
                <span class="text-xs text-white/30">{{ s._open ? '▼' : '▶' }}</span>
              </div>
              <div v-if="s._open" class="px-3 pb-3 border-t border-white/5">
                <div class="flex gap-2 py-2 mb-1">
                  <button @click="mcpSelectAll(s)" class="text-xs px-2 py-0.5 rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30">全選</button>
                  <button @click="mcpDeselectAll(s)" class="text-xs px-2 py-0.5 rounded bg-white/10 text-white/60 hover:bg-white/15">取消</button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
                  <label v-for="t in s.tools" :key="t.name" class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer text-sm">
                    <input type="checkbox" v-model="t.enabled" @change="updateMcpCount(s)" class="w-3.5 h-3.5 accent-cyan-500">
                    <span :class="t.enabled ? 'text-white/90' : 'text-white/40'">{{ t.name }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Skill 配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('skill')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.skill ? '▼' : '▶' }}</span>
            <span class="font-medium">📚 Skill 配置</span>
            <span class="ml-auto text-sm text-white/40">{{ mockSkills.filter(s=>s.enabled).length }}/{{ mockSkills.length }}</span>
          </button>
          <div v-if="open.skill" class="px-4 pb-4 border-t border-white/5">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
              <label v-for="s in mockSkills" :key="s.name" class="flex items-center gap-2 px-3 py-2.5 rounded hover:bg-white/5 cursor-pointer">
                <input type="checkbox" v-model="s.enabled" class="w-4 h-4 accent-cyan-500">
                <span class="text-sm" :class="s.enabled ? 'text-white/90' : 'text-white/40'">{{ s.name }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 4. Cronjob -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('cron')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.cron ? '▼' : '▶' }}</span>
            <span class="font-medium">⏰ Cronjob</span>
            <span class="ml-auto text-sm text-white/40">{{ mockCrons.length }} 筆</span>
          </button>
          <div v-if="open.cron" class="px-4 pb-4 border-t border-white/5">
            <div class="space-y-2">
              <div v-for="(c, i) in visibleCrons" :key="i" class="bg-ocean-700/50 rounded px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-ocean-700/80" @click="editCron(c)">
                <span class="text-sm font-mono text-cyan-400 min-w-[100px]">{{ c.schedule }}</span>
                <span class="text-sm text-white/70 flex-1 truncate">{{ c.message }}</span>
                <span class="text-xs text-white/40 shrink-0">{{ channelMap[c.channel_id] || c.channel_id?.slice(-4) }}</span>
              </div>
            </div>
            <div v-if="mockCrons.length > cronLimit" class="mt-3 text-center">
              <button @click="cronLimit += 20" class="text-sm text-cyan-400 hover:underline">載入更多...</button>
            </div>
            <button @click="editCron(null)" class="mt-3 w-full py-2.5 rounded border border-dashed border-white/20 text-white/50 hover:text-white hover:border-white/40 text-sm">+ 新增 Cronjob</button>
          </div>
        </div>

        <!-- 5. 知識庫配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('kb')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.kb ? '▼' : '▶' }}</span>
            <span class="font-medium">🧠 知識庫配置</span>
            <span class="ml-auto text-sm text-white/40">{{ mockKb.length }} 個</span>
          </button>
          <div v-if="open.kb" class="px-4 pb-4 border-t border-white/5">
            <div class="space-y-2">
              <div v-for="k in mockKb" :key="k.id" class="bg-ocean-700/50 rounded px-4 py-3 flex items-center gap-3">
                <span class="text-cyan-400">📖</span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm text-white/90 truncate">{{ k.name }}</div>
                  <div class="text-xs text-white/40">{{ k.items }} 項 · {{ k.source }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cron Edit Dialog -->
      <div v-if="cronDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="cronDialog = null">
        <div class="bg-ocean-700 rounded-xl w-full max-w-lg p-6 shadow-2xl border border-white/10">
          <h3 class="text-lg font-semibold mb-4">{{ cronDialog.isNew ? '新增' : '編輯' }} Cronjob</h3>
          <div class="space-y-4">
            <Field label="排程時間（Cron 表達式）" tip="5 欄位 POSIX cron：分 時 日 月 週"><input v-model="cronDialog.schedule" class="field-input font-mono" placeholder="0 9 * * 1-5"></Field>
            <Field label="頻道 ID" tip="要發送到的 Discord 頻道"><input v-model="cronDialog.channel_id" class="field-input font-mono" placeholder="1492090122257170526"></Field>
            <Field label="時區" tip="執行時區"><select v-model="cronDialog.timezone" class="field-input"><option>Asia/Taipei</option><option>UTC</option></select></Field>
            <Field label="啟用">
              <div class="flex items-center gap-2"><Toggle v-model="cronDialog.enabled" /><span class="text-sm text-white/70">{{ cronDialog.enabled ? '啟用' : '停用' }}</span></div>
            </Field>
            <Field label="訊息內容" tip="排程觸發時發送的完整 prompt"><textarea v-model="cronDialog.message" rows="6" class="field-input font-mono resize-y" placeholder="排程訊息內容"></textarea></Field>
          </div>
          <div class="flex gap-3 justify-end mt-5">
            <button @click="cronDialog = null" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
            <button @click="cronDialog = null" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">儲存</button>
          </div>
        </div>
      </div>
    </div>
  </AgentDetailLayout>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useAgentList } from '../composables/useAgentList.js'
import AgentDetailLayout from '../components/AgentDetailLayout.vue'
import Field from '../components/Field.vue'
import Toggle from '../components/Toggle.vue'
import TagInput from '../components/TagInput.vue'
import EmojiPicker from '../components/EmojiPicker.vue'

const { agents, selectedAgent, loading, selectAgent } = useAgentList()

const open = reactive({ basic: true, mcp: false, skill: false, cron: false, kb: false })
const cronLimit = ref(20)
const cronDialog = ref(null)

function toggle(key) { open[key] = !open[key] }
function onSelect(a) { selectAgent(a) }

// ID → Name mapping (mock)
const channelMap = { '1492090122257170526': '🍔 蟹堡王', '1503940169252999198': '🏖️ 廣場', '1503704375074361424': '🧪 實驗室' }
const botMap = { '1493800835853975562': '小蝸', '1496023645083009024': '派大星', '1503574146117013555': '泡芙老師' }
const emojiLabels = { thinking: '思考中', tool_use: '使用工具', responding: '回覆中', done: '完成', error: '錯誤', queued: '排隊中', cancelled: '已取消' }

// ─── Mock Data ───
const cfg = reactive({
  discord: { allow_bot_messages: true, allow_user_messages: true, max_bot_turns: 5, allowed_channels: ['1492090122257170526', '1503940169252999198'], allowed_role_ids: [], trusted_bot_ids: ['1493800835853975562'], message_processing_mode: 'buffered', max_buffered_messages: 5, max_batch_tokens: 10000 },
  agent: { command: 'kiro', args: ['chat', '--json'], working_dir: '/home/agent/projects', inherit_env: ['GH_TOKEN', 'AWS_REGION'] },
  pool: { max_sessions: 3, session_ttl_hours: 4 },
  reactions: { enabled: true, remove_after_reply: true, tool_display: 'emoji', emojis: { thinking: '🤔', tool_use: '🔧', responding: '✍️', done: '✅', error: '❌', queued: '📋', cancelled: '🚫' } },
  cron: { usercron_enabled: true, usercron_path: '~/.openab/cronjob.toml' },
})

const mockMcp = reactive([
  { name: 'hrs-mcp', enabled: true, partial: false, _open: false, enabledTools: 7, tools: [{ name: 'GetLeaveBalance', enabled: true }, { name: 'GetLeaveHistory', enabled: true }, { name: 'GetLeavePolicy', enabled: true }, { name: 'SaveLeaveRequest', enabled: true }, { name: 'GetUser', enabled: true }, { name: 'GetDepartment', enabled: true }, { name: 'GetOrganizationCalendar', enabled: true }] },
  { name: 'crm-mcp', enabled: true, partial: false, _open: false, enabledTools: 5, tools: [{ name: 'SearchCustomer', enabled: true }, { name: 'SearchCustomerContact', enabled: true }, { name: 'GetCrmDescription', enabled: true }, { name: 'GetRegionSales', enabled: true }, { name: 'CreateQuote', enabled: true }] },
  { name: 'sap-mcp', enabled: true, partial: true, _open: false, enabledTools: 1, tools: [{ name: 'SearchProductItem', enabled: true }, { name: 'ValidateProductCode', enabled: false }] },
  { name: 'pricing-mcp', enabled: false, partial: false, _open: false, enabledTools: 0, tools: [{ name: 'GetRoomDoorPrice', enabled: false }, { name: 'GetFlooringPrice', enabled: false }] },
  { name: 'image-mcp', enabled: true, partial: false, _open: false, enabledTools: 4, tools: [{ name: 'GenerateImage', enabled: true }, { name: 'ResizeImage', enabled: true }, { name: 'ComposeImage', enabled: true }, { name: 'AddBrandFrame', enabled: true }] },
])

const mcpEnabledCount = computed(() => mockMcp.filter(s => s.enabled).length)
function toggleMcpServer(s) { s.enabled = !s.enabled; s.tools.forEach(t => { t.enabled = s.enabled }); updateMcpCount(s) }
function mcpSelectAll(s) { s.tools.forEach(t => { t.enabled = true }); updateMcpCount(s) }
function mcpDeselectAll(s) { s.tools.forEach(t => { t.enabled = false }); updateMcpCount(s) }
function updateMcpCount(s) { s.enabledTools = s.tools.filter(t => t.enabled).length; s.enabled = s.enabledTools > 0; s.partial = s.enabledTools > 0 && s.enabledTools < s.tools.length }

const mockSkills = reactive([
  { name: 'doc-coauthoring', enabled: true }, { name: 'docx', enabled: true }, { name: 'pdf', enabled: true },
  { name: 'pptx', enabled: true }, { name: 'xlsx', enabled: true }, { name: 'kd-pricing-assistant', enabled: false }, { name: 'kd-product-knowledge', enabled: false },
])

const mockCrons = reactive([
  { schedule: '0 9 * * 1-5', message: '每日站會提醒', channel_id: '1492090122257170526', timezone: 'Asia/Taipei', enabled: true },
  { schedule: '0 18 * * 5', message: '週五下班前確認 PR 狀態', channel_id: '1492090122257170526', timezone: 'Asia/Taipei', enabled: true },
  { schedule: '30 8 * * 1', message: '週一開工打招呼', channel_id: '1503940169252999198', timezone: 'Asia/Taipei', enabled: true },
])
const visibleCrons = computed(() => mockCrons.slice(0, cronLimit.value))
function editCron(c) { cronDialog.value = c ? { ...c, isNew: false } : { schedule: '', message: '', channel_id: '', timezone: 'Asia/Taipei', enabled: true, isNew: true } }

const mockKb = reactive([
  { id: 1, name: '專案清單', items: 12, source: '_projects.md' },
  { id: 2, name: 'AI Chatbox 狀態', items: 8, source: 'ai-chatbox/_status.md' },
  { id: 3, name: 'ALS Vue 狀態', items: 15, source: 'als/als-vue/_status.md' },
])
</script>

<style scoped>
.field-input {
  @apply w-full bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400/50;
}
</style>
