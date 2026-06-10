<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">角色配置</span>
    <button @click="load()" class="ml-auto bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </div>

  <div class="p-7">
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
    </div>

    <div v-else-if="!agents.length" class="text-center py-20 text-white/50">
      <div class="text-4xl mb-3">📭</div>
      <div>此伺服器尚未配置角色</div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <div v-for="a in agents" :key="a.name" :id="'agent-' + a.name"
        class="glass rounded-xl p-4 border-l-4 border-cyan-500/50 transition hover:-translate-y-0.5 hover:shadow-lg flex flex-col">
        <div class="flex items-center gap-3 mb-3">
          <img :src="'/avatar/' + a.name" class="w-11 h-11 rounded-full object-cover border-2 border-white/20" @error="$event.target.style.display='none'">
          <div class="flex-1 min-w-0">
            <div class="font-bold text-base truncate">{{ a.display }}</div>
            <div class="text-sm text-white/50">{{ a.role }}</div>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-2 text-sm mb-3">
          <div class="text-center"><div class="text-lg font-bold text-cyan-300">{{ a.mcp_enabled }}</div><div class="text-[11px] text-white/40">MCP</div></div>
          <div class="text-center"><div class="text-lg font-bold text-cyan-300">{{ a.skills_count }}</div><div class="text-[11px] text-white/40">技能</div></div>
          <div class="text-center"><div class="text-lg font-bold text-cyan-300">{{ a.cronjob_enabled }}</div><div class="text-[11px] text-white/40">排程</div></div>
        </div>

        <button @click="openAgent(a)" class="w-full py-2 text-sm rounded bg-cyan-600/20 border border-cyan-400/30 text-cyan-300 hover:bg-cyan-600/30 font-medium">⚙️ 設定</button>
      </div>
    </div>
  </div>

  <!-- Agent Detail Dialog -->
  <div v-if="selectedAgent" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="closeAgent()">
    <div class="bg-ocean-700 rounded-xl w-[95%] max-w-5xl shadow-2xl flex flex-col" style="height: 85vh;">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-white/10 flex items-center gap-3 shrink-0">
        <img :src="'/avatar/' + selectedAgent.name" class="w-9 h-9 rounded-full object-cover" @error="$event.target.style.display='none'">
        <span class="font-semibold">{{ selectedAgent.display }}</span>
        <span class="text-sm text-white/50">{{ selectedAgent.role }}</span>
        <button @click="closeAgent()" class="ml-auto text-2xl text-white/60 hover:text-white">&times;</button>
      </div>

      <!-- Tabs -->
      <div class="px-6 pt-3 flex gap-1 shrink-0 border-b border-white/5">
        <button v-for="t in detailTabs" :key="t.key" @click="detailTab = t.key"
          :class="detailTab === t.key ? 'bg-cyan-600 text-white' : 'text-white/60 hover:text-white'"
          class="px-3 py-1.5 rounded-t text-xs font-medium transition">{{ t.label }}</button>
      </div>

      <div class="px-6 py-4 flex-1 overflow-y-auto">
        <!-- Config Tab -->
        <div v-if="detailTab === 'config'">
          <div class="flex items-center gap-2 mb-4">
            <button @click="configMode = 'ui'" :class="configMode === 'ui' ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-3 py-1 rounded text-xs">卡片模式</button>
            <button @click="configMode = 'raw'" :class="configMode === 'raw' ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-3 py-1 rounded text-xs">TOML</button>
          </div>

          <div v-if="configMode === 'ui'">
            <div v-if="!configRaw" class="text-white/50 text-sm py-4">無 config.toml</div>
            <div v-else class="space-y-4">
              <!-- Discord Section -->
              <div v-if="configParsed.discord" class="bg-ocean-800/50 rounded-lg p-4">
                <h4 class="text-cyan-300 font-medium text-sm mb-3">🔌 Discord</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div><span class="text-white/50">allow_bot_messages:</span> <span class="text-white ml-1">{{ configParsed.discord.allow_bot_messages }}</span></div>
                  <div><span class="text-white/50">allow_user_messages:</span> <span class="text-white ml-1">{{ configParsed.discord.allow_user_messages }}</span></div>
                  <div><span class="text-white/50">max_bot_turns:</span> <span class="text-white ml-1">{{ configParsed.discord.max_bot_turns }}</span></div>
                  <div class="col-span-2"><span class="text-white/50">allowed_channels:</span> <span class="text-white ml-1">{{ (configParsed.discord.allowed_channels || []).length }} 個</span></div>
                  <div class="col-span-2"><span class="text-white/50">trusted_bot_ids:</span> <span class="text-white ml-1">{{ (configParsed.discord.trusted_bot_ids || []).length }} 個</span></div>
                </div>
              </div>
              <!-- Agent Section -->
              <div v-if="configParsed.agent" class="bg-ocean-800/50 rounded-lg p-4">
                <h4 class="text-cyan-300 font-medium text-sm mb-3">🤖 Agent</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div><span class="text-white/50">command:</span> <span class="text-white ml-1 font-mono">{{ configParsed.agent.command }}</span></div>
                  <div><span class="text-white/50">args:</span> <span class="text-white ml-1 font-mono">{{ (configParsed.agent.args || []).join(' ') }}</span></div>
                  <div class="col-span-2"><span class="text-white/50">working_dir:</span> <span class="text-white ml-1 font-mono">{{ configParsed.agent.working_dir }}</span></div>
                  <div class="col-span-2"><span class="text-white/50">inherit_env:</span> <span class="text-white ml-1">{{ (configParsed.agent.inherit_env || []).length }} 個變數</span></div>
                </div>
              </div>
              <!-- Pool Section -->
              <div v-if="configParsed.pool" class="bg-ocean-800/50 rounded-lg p-4">
                <h4 class="text-cyan-300 font-medium text-sm mb-3">🏊 Pool</h4>
                <div class="grid grid-cols-2 gap-3 text-xs">
                  <div><span class="text-white/50">max_sessions:</span> <span class="text-white ml-1">{{ configParsed.pool.max_sessions }}</span></div>
                  <div><span class="text-white/50">session_ttl_hours:</span> <span class="text-white ml-1">{{ configParsed.pool.session_ttl_hours }}</span></div>
                </div>
              </div>
              <!-- Reactions Section -->
              <div v-if="configParsed.reactions" class="bg-ocean-800/50 rounded-lg p-4">
                <h4 class="text-cyan-300 font-medium text-sm mb-3">😀 Reactions</h4>
                <div class="grid grid-cols-2 gap-3 text-xs">
                  <div><span class="text-white/50">enabled:</span> <span class="ml-1" :class="configParsed.reactions.enabled ? 'text-green-400' : 'text-red-400'">{{ configParsed.reactions.enabled }}</span></div>
                  <div v-if="configParsed.reactions.emojis"><span class="text-white/50">emojis:</span> <span class="text-white ml-1">{{ Object.values(configParsed.reactions.emojis || {}).join(' ') }}</span></div>
                </div>
              </div>
              <!-- Cron Section -->
              <div v-if="configParsed.cron" class="bg-ocean-800/50 rounded-lg p-4">
                <h4 class="text-cyan-300 font-medium text-sm mb-3">⏰ Cron</h4>
                <div class="text-xs"><span class="text-white/50">usercron_enabled:</span> <span class="ml-1" :class="configParsed.cron.usercron_enabled ? 'text-green-400' : 'text-red-400'">{{ configParsed.cron.usercron_enabled }}</span></div>
              </div>
            </div>
          </div>

          <div v-if="configMode === 'raw'">
            <textarea v-model="configRaw" rows="25" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-sm font-mono leading-relaxed resize-y"></textarea>
            <div class="flex items-center gap-3 mt-3">
              <button @click="saveConfig()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-1.5 rounded text-xs font-medium">💾 儲存</button>
              <span v-if="configStatus" class="text-xs" :class="configStatus.ok ? 'text-green-400' : 'text-red-400'">{{ configStatus.text }}</span>
            </div>
          </div>
        </div>

        <!-- MCP Tab -->
        <div v-if="detailTab === 'mcp'">
          <!-- Shuttle UI -->
          <div v-if="!mcpRegistryList.length" class="text-white/50 text-sm py-4">Registry 無 MCP Server，請先到「MCP 管理」新增</div>
          <div v-else class="flex gap-3" style="height: 340px">
            <div class="flex-1 glass rounded-xl flex flex-col overflow-hidden">
              <div class="px-4 py-2 bg-ocean-800/60 text-sm font-medium border-b border-white/10">可用 MCP</div>
              <div class="flex-1 overflow-y-auto p-2 space-y-1">
                <div v-for="s in availableMcps" :key="s.key" @click="toggleLeftSelect(s.key)"
                  :class="leftSelected.includes(s.key) ? 'bg-cyan-600/20 border-cyan-400/50' : 'border-transparent hover:bg-white/5'"
                  class="px-3 py-2 rounded border cursor-pointer flex items-center gap-2">
                  <span class="text-sm">{{ s.name }}</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded" :class="tagColor(s.tags)">{{ s.tags }}</span>
                </div>
              </div>
            </div>
            <div class="flex flex-col items-center justify-center gap-2 w-10">
              <button @click="moveRight()" :disabled="!leftSelected.length" class="w-8 h-8 rounded bg-cyan-600 hover:bg-cyan-500 disabled:opacity-30 text-white font-bold">›</button>
              <button @click="moveLeft()" :disabled="!rightSelected.length" class="w-8 h-8 rounded bg-cyan-600 hover:bg-cyan-500 disabled:opacity-30 text-white font-bold">‹</button>
            </div>
            <div class="flex-1 glass rounded-xl flex flex-col overflow-hidden">
              <div class="px-4 py-2 bg-ocean-800/60 text-sm font-medium border-b border-white/10">已分配 MCP</div>
              <div class="flex-1 overflow-y-auto p-2 space-y-1">
                <div v-for="s in assignedMcps" :key="s.key" @click="toggleRightSelect(s.key)"
                  :class="rightSelected.includes(s.key) ? 'bg-cyan-600/20 border-cyan-400/50' : 'border-transparent hover:bg-white/5'"
                  class="px-3 py-2 rounded border cursor-pointer flex items-center gap-2">
                  <span class="text-sm">{{ s.name }}</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded" :class="tagColor(s.tags)">{{ s.tags }}</span>
                </div>
                <div v-if="!assignedMcps.length" class="text-center text-white/30 text-sm py-8">尚未分配</div>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-3 mt-4">
            <button @click="publishMcpAssignments()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-5 py-2 rounded text-sm font-medium">🚀 發佈到角色</button>
            <span v-if="mcpStatus" class="text-sm" :class="mcpStatus.ok ? 'text-green-400' : 'text-red-400'">{{ mcpStatus.text }}</span>
          </div>

          <!-- Collapsible JSON -->
          <details class="mt-5">
            <summary class="text-sm text-white/50 cursor-pointer hover:text-white/70">進階：直接編輯 JSON</summary>
            <div class="mt-2">
              <textarea v-model="mcpRaw" rows="16" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-sm font-mono leading-relaxed resize-y"></textarea>
              <button @click="saveMcp()" class="mt-2 bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-1.5 rounded text-sm font-medium">💾 儲存 JSON</button>
            </div>
          </details>
        </div>

        <!-- Skills Tab -->
        <div v-if="detailTab === 'skills'">
          <div v-if="!selectedAgent.skills_meta || !selectedAgent.skills_meta.length" class="text-white/50 text-sm py-4">無 Skills</div>
          <div v-else class="space-y-2">
            <div v-for="s in selectedAgent.skills_meta" :key="s.name"
              class="bg-ocean-800/50 rounded-lg px-4 py-3 cursor-pointer hover:bg-ocean-800/70 transition"
              @click="viewSkill(selectedAgent.name, s.name)">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-cyan-400">🧠</span>
                <span class="font-medium text-sm">{{ s.name }}</span>
              </div>
              <div v-if="s.description" class="text-xs text-white/60 line-clamp-2">{{ s.description }}</div>
            </div>
          </div>
        </div>

        <!-- Steering Tab -->
        <div v-if="detailTab === 'steering'">
          <div class="text-xs text-white/50 mb-3">📌 此處唯讀，請透過 Kiro 修改後 commit</div>
          <div v-if="!selectedAgent.steering.length" class="text-white/50 text-sm py-4">無 Steering</div>
          <div v-else class="space-y-1.5">
            <div v-for="f in selectedAgent.steering" :key="f"
              class="bg-ocean-800/50 rounded px-3 py-2 text-sm flex items-center gap-2 cursor-pointer hover:bg-ocean-800/70"
              @click="viewFile(selectedAgent.name, 'steering', f)">
              <span class="text-cyan-400">📋</span>
              <span class="truncate">{{ f }}</span>
            </div>
          </div>
        </div>

        <!-- Cronjob Tab -->
        <div v-if="detailTab === 'cronjob'">
          <div class="flex items-center gap-2 mb-4">
            <button @click="cronMode = 'ui'" :class="cronMode === 'ui' ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-3 py-1 rounded text-xs">視覺化</button>
            <button @click="cronMode = 'raw'" :class="cronMode === 'raw' ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-3 py-1 rounded text-xs">TOML</button>
          </div>

          <div v-if="cronMode === 'ui'">
            <div v-if="!cronJobs.length" class="text-white/50 text-sm py-4">無 Cronjob 配置</div>
            <div v-else class="space-y-2">
              <div v-for="(job, idx) in cronJobs" :key="idx" class="bg-ocean-800/50 rounded-lg p-3">
                <div class="flex items-center gap-3 mb-2">
                  <span class="font-medium text-sm" :class="job.enabled ? 'text-cyan-300' : 'text-white/40 line-through'">
                    {{ job.sender_name || `Job ${idx + 1}` }}
                  </span>
                  <code class="text-xs bg-black/30 text-amber-300 px-2 py-0.5 rounded font-mono">{{ job.schedule }}</code>
                  <span class="text-xs text-white/50">{{ job.timezone || 'UTC' }}</span>
                  <button @click="toggleCron(idx)" class="ml-auto text-xs px-2 py-1 rounded border"
                    :class="job.enabled ? 'border-green-400/30 text-green-300 hover:bg-green-400/10' : 'border-white/20 text-white/60 hover:bg-white/10'">
                    {{ job.enabled ? '✓ 啟用中' : '◌ 已停用' }}
                  </button>
                </div>
                <div class="text-xs text-white/60 mb-1">
                  <span class="text-white/40">channel:</span>
                  <code class="text-cyan-200">{{ job.channel }}</code>
                </div>
                <div v-if="job.message" class="text-xs text-white/70 bg-black/20 rounded p-2 max-h-24 overflow-y-auto whitespace-pre-wrap">{{ job.message.length > 200 ? job.message.slice(0, 200) + '...' : job.message }}</div>
              </div>
            </div>
          </div>

          <div v-if="cronMode === 'raw'">
            <textarea v-model="cronjobContent" rows="20" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-xs font-mono leading-relaxed resize-y"></textarea>
            <div class="flex items-center gap-3 mt-3">
              <button @click="saveCron()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-1.5 rounded text-xs font-medium">💾 儲存</button>
              <span v-if="cronStatus" class="text-xs" :class="cronStatus.ok ? 'text-green-400' : 'text-red-400'">{{ cronStatus.text }}</span>
            </div>
          </div>
        </div>

        <!-- Knowledge Base Tab -->
        <div v-if="detailTab === 'kb'">
          <div v-if="!kbContexts.length" class="text-white/50 text-sm py-4">無 Knowledge Base</div>
          <div v-else class="space-y-2">
            <div v-for="ctx in kbContexts" :key="ctx.id"
              class="bg-ocean-800/50 rounded-lg px-4 py-3 cursor-pointer hover:bg-ocean-800/70"
              @click="viewKb(selectedAgent.name, ctx.id)">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-cyan-400">📚</span>
                <span class="font-medium text-sm">{{ ctx.name }}</span>
                <span v-if="ctx.persistent" class="text-[10px] px-1.5 py-0.5 rounded bg-green-500/20 text-green-300">persistent</span>
                <span v-if="ctx.auto_sync" class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300">auto-sync</span>
                <span class="ml-auto text-xs text-white/50">{{ formatBytes(ctx.size_bytes) }}</span>
              </div>
              <div v-if="ctx.source_path" class="text-xs text-white/50 truncate font-mono">{{ ctx.source_path }}</div>
              <div class="text-[11px] text-white/40 mt-0.5">{{ ctx.item_count }} items · {{ ctx.updated_at ? ctx.updated_at.slice(0, 10) : '-' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Server Dialog -->
    <div v-if="showAddServer" class="fixed inset-0 bg-black/50 z-[70] flex items-center justify-center" @click.self="showAddServer = false">
      <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
        <h3 class="text-lg font-semibold mb-4">新增 MCP Server</h3>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">名稱</label>
          <input v-model="newServer.name" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm" placeholder="例：my-mcp-server">
        </div>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">URL</label>
          <input v-model="newServer.url" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono" placeholder="http://host.docker.internal:1601/mcp/xxx">
        </div>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1">Headers（key: value，每行一個）</label>
          <textarea v-model="newServer.headers" rows="2" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono" placeholder="Authorization: Bearer xxx"></textarea>
        </div>
        <div class="mb-4 flex items-center gap-2">
          <input type="checkbox" v-model="newServer.enabled" id="srv-enabled" class="w-4 h-4 rounded">
          <label for="srv-enabled" class="text-sm text-white/70">新增後立即啟用</label>
        </div>
        <div class="flex gap-3 justify-end">
          <button @click="showAddServer = false" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
          <button @click="addServer()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">新增</button>
        </div>
      </div>
    </div>
  </div>

  <!-- File Viewer -->
  <div v-if="fileView" class="fixed inset-0 bg-black/70 z-[60] flex items-center justify-center" @click.self="fileView = null">
    <div class="bg-ocean-700 rounded-xl w-[90%] max-w-3xl flex flex-col shadow-2xl" style="height: 75vh;">
      <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between font-semibold shrink-0">
        <span class="truncate">{{ fileView.filename }}</span>
        <button @click="fileView = null" class="text-2xl text-white/60 hover:text-white shrink-0 ml-2">&times;</button>
      </div>
      <div class="px-6 py-4 overflow-y-auto flex-1">
        <pre class="text-xs leading-relaxed whitespace-pre-wrap break-words text-white/90 bg-black/30 p-4 rounded-lg">{{ fileView.content }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, put, post } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const loading = ref(false)
const agents = ref([])
const selectedAgent = ref(null)
const detailTab = ref('config')

// MCP state
const mcpRaw = ref('')
const mcpStatus = ref(null)
const mcpRegistryList = ref([])
const mcpAssignedKeys = ref(new Set())
const mcpHasDraft = ref(false)
const configMode = ref('ui')
const configRaw = ref('')
const configStatus = ref(null)
const showAddServer = ref(false)
const newServer = ref({ name: '', url: '', headers: '', enabled: true })

// Cronjob state
const cronMode = ref('ui')
const cronjobContent = ref('')
const cronJobs = ref([])
const cronStatus = ref(null)

// KB state
const kbContexts = ref([])

// File viewer
const fileView = ref(null)

const detailTabs = [
  { key: 'config', label: '⚙️ Config' },
  { key: 'mcp', label: '🔌 MCP' },
  { key: 'skills', label: '🧠 Skills' },
  { key: 'steering', label: '📋 Steering' },
  { key: 'cronjob', label: '⏰ Cronjob' },
  { key: 'kb', label: '📚 Knowledge' },
]

const mcpServersMap = computed(() => {
  try { return JSON.parse(mcpRaw.value)?.mcpServers || {} } catch { return {} }
})
const mcpServers = computed(() => Object.keys(mcpServersMap.value))

function maskToken(val) {
  if (!val || val.length < 8) return '***'
  return val.slice(0, 4) + '***' + val.slice(-4)
}

function formatBytes(b) {
  if (!b) return '0 B'
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'
  return (b / 1024 / 1024).toFixed(1) + ' MB'
}

async function load() {
  loading.value = true
  const res = await get(`/api/agents?group=${currentGroup.value}`)
  agents.value = res?.agents || []
  loading.value = false
  const hash = window.location.hash.replace('#', '')
  if (hash) {
    const a = agents.value.find(x => x.name === hash)
    if (a) openAgent(a)
  }
}

async function openAgent(a) {
  selectedAgent.value = a
  detailTab.value = 'config'
  mcpMode.value = 'ui'
  configMode.value = 'ui'
  cronMode.value = 'ui'
  mcpStatus.value = null
  cronStatus.value = null
  configStatus.value = null
  window.location.hash = a.name
  // Load config.toml
  try {
    const cfgRes = await get(`/api/agents/${a.name}/config`)
    configRaw.value = cfgRes?.raw || ''
  } catch { configRaw.value = '' }
  // Load MCP registry + assignments (fallback to current mcp.json)
  try {
    const regRes = await get('/api/mcp-registry')
    mcpRegistryList.value = regRes?.servers || []
    const assRes = await get(`/api/mcp-assignments/${a.name}`)
    const dbAssignments = assRes?.assignments || []
    if (dbAssignments.length) {
      mcpAssignedKeys.value = new Set(dbAssignments.map(x => x.mcp_key))
    } else {
      // Fallback: read current mcp.json and match keys to registry
      try {
        const raw = JSON.parse(mcpRaw.value || '{}')
        const existingKeys = Object.keys(raw.mcpServers || {})
        const registryKeys = new Set(mcpRegistryList.value.map(s => s.key))
        mcpAssignedKeys.value = new Set(existingKeys.filter(k => registryKeys.has(k)))
      } catch { mcpAssignedKeys.value = new Set() }
    }
    mcpHasDraft.value = dbAssignments.some(x => x.is_draft)
  } catch { mcpRegistryList.value = []; mcpAssignedKeys.value = new Set() }
  // Load MCP
  const res = await get(`/api/agents/${a.name}/mcp`)
  mcpRaw.value = res?.raw || '{}'
  // Load cronjob
  try {
    const cRes = await get(`/api/agents/${a.name}/cronjob`)
    cronjobContent.value = cRes?.content || ''
    cronJobs.value = cRes?.jobs || []
  } catch { cronjobContent.value = ''; cronJobs.value = [] }
  // Load KB contexts
  try {
    const kRes = await get(`/api/agents/${a.name}/kb`)
    kbContexts.value = kRes?.contexts || []
  } catch { kbContexts.value = [] }
}

function closeAgent() {
  selectedAgent.value = null
  history.replaceState(null, '', window.location.pathname)
}

async function saveMcp() {
  mcpStatus.value = null
  try {
    JSON.parse(mcpRaw.value)
  } catch (e) {
    mcpStatus.value = { ok: false, text: `❌ JSON 語法錯誤：${e.message}` }
    return
  }
  const res = await put(`/api/agents/${selectedAgent.value.name}/mcp`, { raw: mcpRaw.value })
  if (res?.ok) { mcpStatus.value = { ok: true, text: '✅ 已儲存' }; load() }
  else mcpStatus.value = { ok: false, text: '❌ ' + (res?.detail || '儲存失敗') }
}

const configParsed = computed(() => {
  if (!configRaw.value) return {}
  try {
    // Simple TOML parser for display — parse sections
    const result = {}
    let section = null
    let subSection = null
    for (const line of configRaw.value.split('\n')) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) continue
      const secMatch = trimmed.match(/^\[([^\]]+)\]$/)
      if (secMatch) {
        const parts = secMatch[1].split('.')
        section = parts[0]
        subSection = parts.length > 1 ? parts.slice(1).join('.') : null
        if (!result[section]) result[section] = {}
        continue
      }
      if (!section) continue
      const kvMatch = trimmed.match(/^(\w+)\s*=\s*(.+)$/)
      if (kvMatch) {
        let val = kvMatch[2].trim()
        // Parse value
        if (val === 'true') val = true
        else if (val === 'false') val = false
        else if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1)
        else if (val.startsWith('[')) try { val = JSON.parse(val.replace(/'/g, '"')) } catch {}
        else if (!isNaN(val)) val = Number(val)
        if (subSection) {
          if (!result[section][subSection]) result[section][subSection] = {}
          result[section][subSection][kvMatch[1]] = val
        } else {
          result[section][kvMatch[1]] = val
        }
      }
    }
    return result
  } catch { return {} }
})

async function saveConfig() {
  configStatus.value = null
  const res = await put(`/api/agents/${selectedAgent.value.name}/config`, { raw: configRaw.value })
  if (res?.ok) configStatus.value = { ok: true, text: '✅ 已儲存' }
  else configStatus.value = { ok: false, text: '❌ ' + (res?.detail || '儲存失敗') }
}

function isMcpAssigned(key) { return mcpAssignedKeys.value.has(key) }

const leftSelected = ref([])
const rightSelected = ref([])
const availableMcps = computed(() => mcpRegistryList.value.filter(s => !mcpAssignedKeys.value.has(s.key)))
const assignedMcps = computed(() => mcpRegistryList.value.filter(s => mcpAssignedKeys.value.has(s.key)))

function tagColor(tag) {
  if (tag === '正式') return 'bg-green-500/20 text-green-300'
  if (tag === '測試') return 'bg-amber-500/20 text-amber-300'
  if (tag === '本地') return 'bg-blue-500/20 text-blue-300'
  return 'bg-white/10 text-white/60'
}

function toggleLeftSelect(key) { const i = leftSelected.value.indexOf(key); i >= 0 ? leftSelected.value.splice(i, 1) : leftSelected.value.push(key) }
function toggleRightSelect(key) { const i = rightSelected.value.indexOf(key); i >= 0 ? rightSelected.value.splice(i, 1) : rightSelected.value.push(key) }

function moveRight() {
  const s = new Set(mcpAssignedKeys.value)
  leftSelected.value.forEach(k => s.add(k))
  mcpAssignedKeys.value = s
  leftSelected.value = []
  saveDraft()
}
function moveLeft() {
  const s = new Set(mcpAssignedKeys.value)
  rightSelected.value.forEach(k => s.delete(k))
  mcpAssignedKeys.value = s
  rightSelected.value = []
  saveDraft()
}
function saveDraft() {
  const assignments = [...mcpAssignedKeys.value].map(k => ({ mcp_key: k, enabled: true, allowed_tools: [] }))
  put(`/api/mcp-assignments/${selectedAgent.value.name}`, { assignments })
}

function toggleMcpAssign(key, checked) {
  const s = new Set(mcpAssignedKeys.value)
  if (checked) s.add(key); else s.delete(key)
  mcpAssignedKeys.value = s
  saveDraft()
}

async function publishMcpAssignments() {
  mcpStatus.value = null
  const res = await post(`/api/mcp-assignments/${selectedAgent.value.name}/publish`)
  if (res?.ok) { mcpStatus.value = { ok: true, text: '✅ 已發佈' }; mcpHasDraft.value = false }
  else mcpStatus.value = { ok: false, text: '❌ ' + (res?.detail || '發佈失敗') }
}

function toggleServer(name) {
  try {
    const config = JSON.parse(mcpRaw.value)
    if (config.mcpServers && config.mcpServers[name]) {
      config.mcpServers[name].disabled = !config.mcpServers[name].disabled
      mcpRaw.value = JSON.stringify(config, null, 2)
      saveMcp()
    }
  } catch {}
}

function updateServerField(name, field, value) {
  try {
    const config = JSON.parse(mcpRaw.value)
    if (config.mcpServers && config.mcpServers[name]) {
      config.mcpServers[name][field] = value
      mcpRaw.value = JSON.stringify(config, null, 2)
      saveMcp()
    }
  } catch {}
}

function removeServer(name) {
  if (!confirm(`確定要刪除 MCP Server「${name}」？`)) return
  try {
    const config = JSON.parse(mcpRaw.value)
    if (config.mcpServers) {
      delete config.mcpServers[name]
      mcpRaw.value = JSON.stringify(config, null, 2)
      saveMcp()
    }
  } catch {}
}

function addServer() {
  if (!newServer.value.name || !newServer.value.url) return
  try {
    const config = JSON.parse(mcpRaw.value) || {}
    if (!config.mcpServers) config.mcpServers = {}
    const srv = { url: newServer.value.url, disabled: !newServer.value.enabled }
    const headers = {}
    newServer.value.headers.split('\n').forEach(line => {
      const idx = line.indexOf(':')
      if (idx > 0) headers[line.slice(0, idx).trim()] = line.slice(idx + 1).trim()
    })
    if (Object.keys(headers).length) srv.headers = headers
    config.mcpServers[newServer.value.name] = srv
    mcpRaw.value = JSON.stringify(config, null, 2)
    saveMcp()
    showAddServer.value = false
    newServer.value = { name: '', url: '', headers: '', enabled: true }
  } catch {}
}

async function toggleCron(idx) {
  const res = await put(`/api/agents/${selectedAgent.value.name}/cronjob/${idx}/toggle`, {})
  if (res?.ok) {
    cronJobs.value = res.jobs || []
    // Reload raw too
    const cRes = await get(`/api/agents/${selectedAgent.value.name}/cronjob`)
    cronjobContent.value = cRes?.content || ''
    load()
  }
}

async function saveCron() {
  cronStatus.value = null
  const res = await put(`/api/agents/${selectedAgent.value.name}/cronjob`, { content: cronjobContent.value })
  if (res?.ok) {
    cronStatus.value = { ok: true, text: '✅ 已儲存' }
    const cRes = await get(`/api/agents/${selectedAgent.value.name}/cronjob`)
    cronJobs.value = cRes?.jobs || []
    load()
  } else {
    cronStatus.value = { ok: false, text: '❌ ' + (res?.detail || '儲存失敗') }
  }
}

async function viewFile(agent, type, filename) {
  const res = await get(`/api/agents/${agent}/${type}/${filename}`)
  if (res?.content) fileView.value = { filename, content: res.content }
}

async function viewSkill(agent, skillName) {
  const res = await get(`/api/agents/${agent}/skills/${skillName}`)
  if (res?.content) fileView.value = { filename: res.filename, content: res.content }
  else fileView.value = { filename: skillName, content: '(無 SKILL.md 內容)' }
}

async function viewKb(agent, kbId) {
  const res = await get(`/api/agents/${agent}/kb/${kbId}`)
  if (!res) return
  const ctx = res.context || {}
  const header = `名稱：${ctx.name}\n描述：${ctx.description || '-'}\n來源：${ctx.source_path || '-'}\n項目數：${ctx.item_count || 0}\n更新時間：${ctx.updated_at || '-'}\n\n${'='.repeat(60)}\n\n`
  const body = res.content_error ? `⚠️ ${res.content_error}` : (res.content || '(空)')
  fileView.value = { filename: ctx.name || kbId, content: header + body }
}

window.addEventListener('hashchange', () => {
  const hash = window.location.hash.replace('#', '')
  if (hash && agents.value.length) {
    const a = agents.value.find(x => x.name === hash)
    if (a && (!selectedAgent.value || selectedAgent.value.name !== a.name)) openAgent(a)
  } else if (!hash) {
    selectedAgent.value = null
  }
})

watch(currentGroup, () => { selectedAgent.value = null; load() })
onMounted(() => {
  load()
  window.addEventListener('group-changed', load)
})
</script>
