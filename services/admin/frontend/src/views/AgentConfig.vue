<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">角色配置</span>
    <button @click="load()" class="ml-auto bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </div>

  <div class="p-7">
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
    </div>

    <!-- Agent Cards Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="a in agents" :key="a.name" :id="'agent-' + a.name"
        class="glass rounded-xl p-5 border-l-4 border-cyan-500/50 cursor-pointer transition hover:-translate-y-0.5 hover:shadow-lg"
        @click="openAgent(a)">
        <div class="flex items-center gap-3 mb-3">
          <img :src="'/avatar/' + a.name" class="w-10 h-10 rounded-full object-cover border-2 border-white/20" @error="$event.target.style.display='none'">
          <div class="flex-1 min-w-0">
            <div class="font-semibold truncate">{{ a.display }}</div>
            <div class="text-sm text-white/60 truncate" :title="a.role">{{ a.role }}</div>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-2 text-xs text-white/70">
          <div title="MCP Servers">🔌 {{ a.mcp_servers }}</div>
          <div title="Skills">🧠 {{ a.skills_count }}</div>
          <div title="Steering">📋 {{ a.steering_count }}</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Agent Detail Dialog -->
  <div v-if="selectedAgent" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="selectedAgent = null">
    <div class="bg-ocean-700 rounded-xl w-[95%] max-w-4xl max-h-[85vh] flex flex-col shadow-2xl">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-white/10 flex items-center gap-3 shrink-0">
        <img :src="'/avatar/' + selectedAgent.name" class="w-8 h-8 rounded-full object-cover" @error="$event.target.style.display='none'">
        <span class="font-semibold">{{ selectedAgent.display }}</span>
        <span class="text-sm text-white/50">{{ selectedAgent.role }}</span>
        <button @click="selectedAgent = null" class="ml-auto text-2xl text-white/60 hover:text-white">&times;</button>
      </div>

      <!-- Tabs -->
      <div class="px-6 pt-3 flex gap-1 shrink-0">
        <button v-for="t in detailTabs" :key="t.key" @click="detailTab = t.key"
          :class="detailTab === t.key ? 'bg-cyan-600 text-white' : 'text-white/60 hover:text-white'"
          class="px-3 py-1.5 rounded text-xs font-medium transition">{{ t.label }}</button>
      </div>

      <!-- Content -->
      <div class="px-6 py-4 flex-1 overflow-y-auto">
        <!-- MCP Tab -->
        <div v-if="detailTab === 'mcp'">
          <div class="flex items-center gap-2 mb-4">
            <button @click="mcpMode = 'ui'" :class="mcpMode === 'ui' ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-3 py-1 rounded text-xs">管理模式</button>
            <button @click="mcpMode = 'raw'" :class="mcpMode === 'raw' ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-3 py-1 rounded text-xs">JSON</button>
            <button v-if="mcpMode === 'ui'" @click="showAddServer = true" class="ml-auto text-xs px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white">+ 新增 Server</button>
          </div>

          <!-- UI Mode -->
          <div v-if="mcpMode === 'ui'" class="space-y-3">
            <div v-if="!mcpServers.length" class="text-white/50 text-sm py-4">無 MCP Server 配置</div>
            <div v-for="name in mcpServers" :key="name" class="bg-ocean-800/50 rounded-lg p-4">
              <div class="flex items-center gap-3 mb-2">
                <span class="font-medium text-sm" :class="mcpServersMap[name].disabled ? 'text-white/40 line-through' : 'text-cyan-300'">{{ name }}</span>
                <span v-if="mcpServersMap[name].disabled" class="text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-300">停用</span>
                <span v-else class="text-xs px-1.5 py-0.5 rounded bg-green-500/20 text-green-300">啟用</span>
                <div class="ml-auto flex gap-2">
                  <button @click="toggleServer(name)" class="text-xs px-2 py-1 rounded border border-white/20 hover:bg-white/10">
                    {{ mcpServersMap[name].disabled ? '啟用' : '停用' }}
                  </button>
                  <button @click="removeServer(name)" class="text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10">刪除</button>
                </div>
              </div>
              <div class="grid grid-cols-1 gap-1.5 text-xs">
                <div class="flex items-center gap-2">
                  <span class="text-white/40 min-w-[60px]">command</span>
                  <span class="text-white/80 font-mono">{{ mcpServersMap[name].command || '-' }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-white/40 min-w-[60px]">args</span>
                  <span class="text-white/80 font-mono truncate">{{ (mcpServersMap[name].args || []).join(' ') || '-' }}</span>
                </div>
                <div v-if="mcpServersMap[name].env" class="flex items-start gap-2">
                  <span class="text-white/40 min-w-[60px]">env</span>
                  <span class="text-white/80 font-mono text-[11px]">{{ Object.keys(mcpServersMap[name].env).join(', ') }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Raw Mode -->
          <div v-if="mcpMode === 'raw'">
            <textarea v-model="mcpRaw" rows="18" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-xs font-mono leading-relaxed resize-y"></textarea>
            <div class="flex items-center gap-3 mt-3">
              <button @click="saveMcp()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-1.5 rounded text-xs font-medium">💾 儲存</button>
              <span v-if="mcpStatus" class="text-xs" :class="mcpStatus.ok ? 'text-green-400' : 'text-red-400'">{{ mcpStatus.text }}</span>
            </div>
          </div>

          <!-- Add Server Dialog -->
          <div v-if="showAddServer" class="fixed inset-0 bg-black/50 z-[70] flex items-center justify-center" @click.self="showAddServer = false">
            <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
              <h3 class="text-lg font-semibold mb-4">新增 MCP Server</h3>
              <div class="mb-3">
                <label class="block text-sm text-white/70 mb-1">名稱</label>
                <input v-model="newServer.name" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm" placeholder="例：my-server">
              </div>
              <div class="mb-3">
                <label class="block text-sm text-white/70 mb-1">Command</label>
                <input v-model="newServer.command" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm" placeholder="例：uvx 或 npx">
              </div>
              <div class="mb-3">
                <label class="block text-sm text-white/70 mb-1">Args（每行一個）</label>
                <textarea v-model="newServer.args" rows="3" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono" placeholder="例：my-package@latest&#10;--option"></textarea>
              </div>
              <div class="mb-4">
                <label class="block text-sm text-white/70 mb-1">ENV（key=value，每行一個）</label>
                <textarea v-model="newServer.env" rows="2" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono" placeholder="例：API_KEY=xxx"></textarea>
              </div>
              <div class="flex gap-3 justify-end">
                <button @click="showAddServer = false" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
                <button @click="addServer()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">新增</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Skills Tab -->
        <div v-if="detailTab === 'skills'">
          <div v-if="!selectedAgent.skills.length" class="text-white/50 text-sm py-4">無 Skills</div>
          <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-2">
            <div v-for="s in selectedAgent.skills" :key="s" class="bg-ocean-800/50 rounded px-3 py-2 text-sm flex items-center gap-2">
              <span class="text-cyan-400">🧠</span>
              <span class="truncate">{{ s }}</span>
            </div>
          </div>
        </div>

        <!-- Steering Tab -->
        <div v-if="detailTab === 'steering'">
          <div v-if="!selectedAgent.steering.length" class="text-white/50 text-sm py-4">無 Steering</div>
          <div v-else class="space-y-1.5">
            <div v-for="f in selectedAgent.steering" :key="f" class="bg-ocean-800/50 rounded px-3 py-2 text-sm flex items-center gap-2 cursor-pointer hover:bg-ocean-800" @click="viewFile(selectedAgent.name, 'steering', f)">
              <span class="text-cyan-400">📋</span>
              <span class="truncate">{{ f }}</span>
            </div>
          </div>
        </div>

        <!-- Cronjob Tab -->
        <div v-if="detailTab === 'cronjob'">
          <div v-if="!cronjobContent" class="text-white/50 text-sm py-4">無 Cronjob 配置</div>
          <pre v-else class="text-xs leading-relaxed whitespace-pre-wrap text-white/90 bg-ocean-800/50 p-4 rounded-lg font-mono">{{ cronjobContent }}</pre>
        </div>

        <!-- Knowledge Base Tab -->
        <div v-if="detailTab === 'kb'">
          <div v-if="!kbFiles.length" class="text-white/50 text-sm py-4">無 Knowledge Base 檔案</div>
          <div v-else class="space-y-1.5">
            <div v-for="f in kbFiles" :key="f" class="bg-ocean-800/50 rounded px-3 py-2 text-sm flex items-center gap-2">
              <span class="text-cyan-400">📚</span>
              <span class="truncate">{{ f }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- File Viewer -->
  <div v-if="fileView" class="fixed inset-0 bg-black/70 z-[60] flex items-center justify-center" @click.self="fileView = null">
    <div class="bg-ocean-700 rounded-xl w-[90%] max-w-3xl max-h-[80vh] flex flex-col shadow-2xl">
      <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between font-semibold shrink-0">
        <span>{{ fileView.filename }}</span>
        <button @click="fileView = null" class="text-2xl text-white/60 hover:text-white">&times;</button>
      </div>
      <div class="px-6 py-4 overflow-y-auto flex-1">
        <pre class="text-xs leading-relaxed whitespace-pre-wrap break-words text-white/90 bg-black/30 p-4 rounded-lg">{{ fileView.content }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, put } = useApi()

const loading = ref(false)
const agents = ref([])
const selectedAgent = ref(null)
const detailTab = ref('mcp')
const mcpMode = ref('ui')
const mcpRaw = ref('')
const mcpStatus = ref(null)
const showAddServer = ref(false)
const newServer = ref({ name: '', command: '', args: '', env: '' })
const cronjobContent = ref('')
const kbFiles = ref([])
const fileView = ref(null)

const detailTabs = [
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

async function load() {
  loading.value = true
  const res = await get('/api/agents')
  agents.value = res?.agents || []
  loading.value = false
  // Auto-open if hash
  const hash = window.location.hash.replace('#', '')
  if (hash) {
    const a = agents.value.find(x => x.name === hash)
    if (a) openAgent(a)
  }
}

async function openAgent(a) {
  selectedAgent.value = a
  detailTab.value = 'mcp'
  mcpMode.value = 'ui'
  mcpStatus.value = null
  // Load MCP
  const res = await get(`/api/agents/${a.name}/mcp`)
  mcpRaw.value = res?.raw || '{}'
  // Load cronjob
  try {
    const cRes = await get(`/api/agents/${a.name}/cronjob`)
    cronjobContent.value = cRes?.content || ''
  } catch { cronjobContent.value = '' }
  // Load KB
  try {
    const kRes = await get(`/api/agents/${a.name}/kb`)
    kbFiles.value = kRes?.files || []
  } catch { kbFiles.value = [] }
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
  if (!newServer.value.name || !newServer.value.command) return
  try {
    const config = JSON.parse(mcpRaw.value) || {}
    if (!config.mcpServers) config.mcpServers = {}
    const args = newServer.value.args.split('\n').map(a => a.trim()).filter(Boolean)
    const env = {}
    newServer.value.env.split('\n').forEach(line => {
      const [k, ...v] = line.split('=')
      if (k && v.length) env[k.trim()] = v.join('=').trim()
    })
    config.mcpServers[newServer.value.name] = {
      command: newServer.value.command,
      args: args.length ? args : undefined,
      env: Object.keys(env).length ? env : undefined,
      disabled: false,
    }
    mcpRaw.value = JSON.stringify(config, null, 2)
    saveMcp()
    showAddServer.value = false
    newServer.value = { name: '', command: '', args: '', env: '' }
  } catch {}
}

async function viewFile(agent, type, filename) {
  const res = await get(`/api/agents/${agent}/${type}/${filename}`)
  if (res?.content) fileView.value = { filename, content: res.content }
}

onMounted(load)
</script>
