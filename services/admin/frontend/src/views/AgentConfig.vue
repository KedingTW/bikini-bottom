<template>
  <AgentDetailLayout :agents="agents" :selected-agent="selectedAgent" :loading="loading" @select="onSelect" @back="selectedAgent = null">
    <div v-if="!selectedAgent" class="text-center py-20 text-white/50 hidden md:block">
      <div class="text-3xl mb-2">🤖</div>
      <div>請選擇角色查看配置</div>
    </div>

    <div v-if="selectedAgent">
      <h2 class="text-lg font-semibold mb-4">{{ selectedAgent.display }} 配置</h2>

      <!-- Accordion Sections -->
      <div class="space-y-2">
        <!-- 1. 基本配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('basic')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.basic ? '▼' : '▶' }}</span>
            <span class="font-medium text-sm">⚙️ 基本配置</span>
            <button @click.stop class="ml-auto text-[10px] px-2 py-0.5 rounded bg-ocean-700 border border-white/15 text-white/60 hover:text-white">📂 工作目錄</button>
          </button>
          <div v-if="open.basic" class="px-4 pb-4 border-t border-white/5 space-y-4">
            <!-- Discord -->
            <fieldset class="border border-white/10 rounded-lg p-3">
              <legend class="text-xs text-cyan-400 px-1">Discord</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <Field label="allow_bot_messages" tip="是否接收 bot 訊息"><select v-model="cfg.discord.allow_bot_messages" class="field-input"><option :value="true">true</option><option :value="false">false</option></select></Field>
                <Field label="allow_user_messages" tip="是否接收使用者訊息"><select v-model="cfg.discord.allow_user_messages" class="field-input"><option :value="true">true</option><option :value="false">false</option></select></Field>
                <Field label="max_bot_turns" tip="Bot 對話最大輪數"><input v-model.number="cfg.discord.max_bot_turns" type="number" class="field-input"></Field>
                <Field label="message_processing_mode" tip="訊息處理模式"><select v-model="cfg.discord.message_processing_mode" class="field-input"><option>buffered</option><option>immediate</option></select></Field>
                <Field label="max_buffered_messages" tip="緩衝訊息數上限"><input v-model.number="cfg.discord.max_buffered_messages" type="number" class="field-input"></Field>
                <Field label="max_batch_tokens" tip="批次 token 上限"><input v-model.number="cfg.discord.max_batch_tokens" type="number" class="field-input"></Field>
              </div>
              <div class="mt-3 space-y-2">
                <Field label="allowed_channels" tip="允許的頻道 ID"><TagInput v-model="cfg.discord.allowed_channels" /></Field>
                <Field label="allowed_role_ids" tip="允許的身分組 ID"><TagInput v-model="cfg.discord.allowed_role_ids" /></Field>
                <Field label="trusted_bot_ids" tip="信任的 Bot ID"><TagInput v-model="cfg.discord.trusted_bot_ids" /></Field>
              </div>
            </fieldset>
            <!-- Agent -->
            <fieldset class="border border-white/10 rounded-lg p-3">
              <legend class="text-xs text-cyan-400 px-1">Agent</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Field label="command" tip="啟動指令"><input v-model="cfg.agent.command" class="field-input font-mono"></Field>
                <Field label="working_dir" tip="工作目錄"><input v-model="cfg.agent.working_dir" class="field-input font-mono"></Field>
              </div>
              <div class="mt-3">
                <Field label="args" tip="啟動參數"><TagInput v-model="cfg.agent.args" /></Field>
                <Field label="inherit_env" tip="繼承的環境變數"><TagInput v-model="cfg.agent.inherit_env" /></Field>
              </div>
            </fieldset>
            <!-- Pool -->
            <fieldset class="border border-white/10 rounded-lg p-3">
              <legend class="text-xs text-cyan-400 px-1">Pool</legend>
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <Field label="max_sessions" tip="最大 session 數"><input v-model.number="cfg.pool.max_sessions" type="number" class="field-input"></Field>
                <Field label="session_ttl_hours" tip="Session 存活時數"><input v-model.number="cfg.pool.session_ttl_hours" type="number" class="field-input"></Field>
              </div>
            </fieldset>
            <!-- Reactions -->
            <fieldset class="border border-white/10 rounded-lg p-3">
              <legend class="text-xs text-cyan-400 px-1">Reactions</legend>
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <Field label="enabled" tip="啟用反應"><Toggle v-model="cfg.reactions.enabled" /></Field>
                <Field label="remove_after_reply" tip="回覆後移除"><Toggle v-model="cfg.reactions.remove_after_reply" /></Field>
                <Field label="tool_display" tip="工具顯示模式"><select v-model="cfg.reactions.tool_display" class="field-input"><option>emoji</option><option>text</option><option>none</option></select></Field>
              </div>
              <div class="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
                <Field v-for="(val, key) in cfg.reactions.emojis" :key="key" :label="key" :tip="'Emoji: '+key"><input v-model="cfg.reactions.emojis[key]" class="field-input text-center"></Field>
              </div>
            </fieldset>
            <!-- STT -->
            <fieldset class="border border-white/10 rounded-lg p-3">
              <legend class="text-xs text-cyan-400 px-1">STT</legend>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Field label="enabled" tip="啟用語音轉文字"><Toggle v-model="cfg.stt.enabled" /></Field>
                <Field label="model" tip="STT 模型"><input v-model="cfg.stt.model" class="field-input font-mono"></Field>
                <Field label="base_url" tip="STT API URL"><input v-model="cfg.stt.base_url" class="field-input font-mono"></Field>
              </div>
            </fieldset>
            <!-- Cron -->
            <fieldset class="border border-white/10 rounded-lg p-3">
              <legend class="text-xs text-cyan-400 px-1">Cron 設定</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Field label="usercron_enabled" tip="啟用使用者排程"><Toggle v-model="cfg.cron.usercron_enabled" /></Field>
                <Field label="usercron_path" tip="排程檔案路徑"><input v-model="cfg.cron.usercron_path" class="field-input font-mono"></Field>
              </div>
            </fieldset>
          </div>
        </div>

        <!-- 2. MCP 配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('mcp')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.mcp ? '▼' : '▶' }}</span>
            <span class="font-medium text-sm">🔌 MCP 配置</span>
            <span class="ml-auto text-xs text-white/40">{{ mcpEnabledCount }}/{{ mockMcp.length }}</span>
          </button>
          <div v-if="open.mcp" class="px-4 pb-4 border-t border-white/5 space-y-2">
            <div v-for="s in mockMcp" :key="s.name" class="bg-ocean-700/50 rounded-lg overflow-hidden">
              <div class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-white/5" @click="s._open = !s._open">
                <input type="checkbox" :checked="s.enabled" :indeterminate="s.partial" @click.stop="toggleMcpServer(s)" class="w-4 h-4 accent-cyan-500">
                <span class="text-sm flex-1" :class="s.enabled ? 'text-cyan-300' : 'text-white/40'">{{ s.name }}</span>
                <span class="text-[10px] text-white/40">{{ s.enabledTools }}/{{ s.tools.length }}</span>
                <span class="text-xs text-white/30">{{ s._open ? '▼' : '▶' }}</span>
              </div>
              <div v-if="s._open" class="px-3 pb-2 border-t border-white/5">
                <div class="flex gap-2 py-1.5 mb-1">
                  <button @click="mcpSelectAll(s)" class="text-[10px] px-2 py-0.5 rounded bg-cyan-600/20 text-cyan-300">全選</button>
                  <button @click="mcpDeselectAll(s)" class="text-[10px] px-2 py-0.5 rounded bg-white/10 text-white/60">取消</button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-0.5">
                  <label v-for="t in s.tools" :key="t.name" class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-white/5 cursor-pointer text-xs">
                    <input type="checkbox" v-model="t.enabled" @change="updateMcpCount(s)" class="w-3 h-3 accent-cyan-500">
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
            <span class="font-medium text-sm">📚 Skill 配置</span>
            <span class="ml-auto text-xs text-white/40">{{ mockSkills.filter(s=>s.enabled).length }}/{{ mockSkills.length }}</span>
          </button>
          <div v-if="open.skill" class="px-4 pb-4 border-t border-white/5">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
              <label v-for="s in mockSkills" :key="s.name" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-white/5 cursor-pointer text-sm">
                <input type="checkbox" v-model="s.enabled" class="w-4 h-4 accent-cyan-500">
                <span :class="s.enabled ? 'text-white/90' : 'text-white/40'">{{ s.name }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 4. Cronjob -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('cron')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.cron ? '▼' : '▶' }}</span>
            <span class="font-medium text-sm">⏰ Cronjob</span>
            <span class="ml-auto text-xs text-white/40">{{ mockCrons.length }} 筆</span>
          </button>
          <div v-if="open.cron" class="px-4 pb-4 border-t border-white/5">
            <div class="space-y-2">
              <div v-for="(c, i) in visibleCrons" :key="i" class="bg-ocean-700/50 rounded px-3 py-2 flex items-center gap-3 cursor-pointer hover:bg-ocean-700/80" @click="editCron(c)">
                <span class="text-xs font-mono text-cyan-400 min-w-[80px]">{{ c.schedule }}</span>
                <span class="text-xs text-white/70 flex-1 truncate">{{ c.message }}</span>
                <span class="text-[10px] text-white/40 shrink-0">{{ c.channel_id?.slice(-4) }}</span>
              </div>
            </div>
            <div v-if="mockCrons.length > cronLimit" class="mt-2 text-center">
              <button @click="cronLimit += 20" class="text-xs text-cyan-400 hover:underline">載入更多...</button>
            </div>
            <button @click="editCron(null)" class="mt-3 w-full py-2 text-xs rounded border border-dashed border-white/20 text-white/50 hover:text-white hover:border-white/40">+ 新增 Cronjob</button>
          </div>
        </div>

        <!-- 5. 知識庫配置 -->
        <div class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <button @click="toggle('kb')" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 text-left">
            <span class="text-white/30">{{ open.kb ? '▼' : '▶' }}</span>
            <span class="font-medium text-sm">🧠 知識庫配置</span>
            <span class="ml-auto text-xs text-white/40">{{ mockKb.length }} 個</span>
          </button>
          <div v-if="open.kb" class="px-4 pb-4 border-t border-white/5">
            <div class="space-y-2">
              <div v-for="k in mockKb" :key="k.id" class="bg-ocean-700/50 rounded px-3 py-2 flex items-center gap-3">
                <span class="text-cyan-400">📖</span>
                <div class="flex-1 min-w-0">
                  <div class="text-sm text-white/90 truncate">{{ k.name }}</div>
                  <div class="text-[10px] text-white/40">{{ k.items }} 項 · {{ k.source }}</div>
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
          <div class="space-y-3">
            <Field label="schedule"><input v-model="cronDialog.schedule" class="field-input font-mono" placeholder="0 9 * * 1-5"></Field>
            <Field label="channel_id"><input v-model="cronDialog.channel_id" class="field-input font-mono" placeholder="1492090122257170526"></Field>
            <Field label="message"><textarea v-model="cronDialog.message" rows="5" class="field-input font-mono resize-y" placeholder="排程訊息內容"></textarea></Field>
          </div>
          <div class="flex gap-3 justify-end mt-4">
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

const { agents, selectedAgent, loading, selectAgent } = useAgentList()

const open = reactive({ basic: true, mcp: false, skill: false, cron: false, kb: false })
const cronLimit = ref(20)
const cronDialog = ref(null)

function toggle(key) { open[key] = !open[key] }
function onSelect(a) { selectAgent(a) }

// ─── Mock Data ───
const cfg = reactive({
  discord: { allow_bot_messages: true, allow_user_messages: true, max_bot_turns: 5, allowed_channels: ['1492090122257170526', '1503940169252999198'], allowed_role_ids: [], trusted_bot_ids: ['1493800835853975562'], message_processing_mode: 'buffered', max_buffered_messages: 5, max_batch_tokens: 10000 },
  agent: { command: 'kiro', args: ['chat', '--json'], working_dir: '/home/agent/projects', inherit_env: ['GH_TOKEN', 'AWS_REGION'] },
  pool: { max_sessions: 3, session_ttl_hours: 4 },
  reactions: { enabled: true, remove_after_reply: true, tool_display: 'emoji', emojis: { thinking: '🤔', tool_use: '🔧', responding: '✍️', done: '✅', error: '❌', queued: '📋', cancelled: '🚫' } },
  stt: { enabled: false, model: 'whisper-large-v3', base_url: 'http://stt.twkd.com:8080' },
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

function toggleMcpServer(s) {
  s.enabled = !s.enabled
  s.tools.forEach(t => { t.enabled = s.enabled })
  updateMcpCount(s)
}
function mcpSelectAll(s) { s.tools.forEach(t => { t.enabled = true }); updateMcpCount(s) }
function mcpDeselectAll(s) { s.tools.forEach(t => { t.enabled = false }); updateMcpCount(s) }
function updateMcpCount(s) {
  s.enabledTools = s.tools.filter(t => t.enabled).length
  s.enabled = s.enabledTools > 0
  s.partial = s.enabledTools > 0 && s.enabledTools < s.tools.length
}

const mockSkills = reactive([
  { name: 'doc-coauthoring', enabled: true },
  { name: 'docx', enabled: true },
  { name: 'pdf', enabled: true },
  { name: 'pptx', enabled: true },
  { name: 'xlsx', enabled: true },
  { name: 'kd-pricing-assistant', enabled: false },
  { name: 'kd-product-knowledge', enabled: false },
])

const mockCrons = reactive([
  { schedule: '0 9 * * 1-5', message: '每日站會提醒', channel_id: '1492090122257170526' },
  { schedule: '0 18 * * 5', message: '週五下班前確認 PR 狀態', channel_id: '1492090122257170526' },
  { schedule: '30 8 * * 1', message: '週一開工打招呼', channel_id: '1503940169252999198' },
])

const visibleCrons = computed(() => mockCrons.slice(0, cronLimit.value))

function editCron(c) {
  cronDialog.value = c ? { ...c, isNew: false } : { schedule: '', message: '', channel_id: '', isNew: true }
}

const mockKb = reactive([
  { id: 1, name: '專案清單', items: 12, source: '_projects.md' },
  { id: 2, name: 'AI Chatbox 狀態', items: 8, source: 'ai-chatbox/_status.md' },
  { id: 3, name: 'ALS Vue 狀態', items: 15, source: 'als/als-vue/_status.md' },
])
</script>

<style scoped>
.field-input {
  @apply w-full bg-ocean-800 border border-white/15 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-400/50;
}
</style>
