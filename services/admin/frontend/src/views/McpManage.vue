<template>
  <AgentDetailLayout :agents="agents" :selected-agent="selectedAgent" :loading="loading" @select="onSelect" @back="selectedAgent = null">
    <div v-if="!selectedAgent" class="text-center py-20 text-white/50 hidden md:block">
      <div class="text-3xl mb-2">🔌</div>
      <div>請選擇角色管理 MCP 配置</div>
    </div>

    <div v-if="selectedAgent">
      <!-- Header -->
      <div class="flex items-center gap-3 mb-5 flex-wrap">
        <h2 class="text-lg font-semibold">{{ selectedAgent.display }} — MCP 配置</h2>
        <button @click="save()" :disabled="saving" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-50">
          {{ saving ? '儲存中...' : '💾 儲存' }}
        </button>
      </div>

      <div v-if="status" class="mb-4 px-4 py-2 rounded-lg text-sm" :class="status.ok ? 'bg-green-500/15 text-green-300' : 'bg-red-500/15 text-red-300'">{{ status.text }}</div>

      <!-- Pool loading -->
      <div v-if="poolLoading" class="text-white/50 text-sm py-4">載入 Pool 中...</div>

      <!-- Server list from MySQL -->
      <div v-else class="space-y-2">
        <div v-for="s in poolServers" :key="s.id" class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <!-- Server header -->
          <div class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/5" @click="toggleExpand(s.id)">
            <input type="checkbox" :checked="isEnabled(s.id)" @click.stop="toggleServer(s.id)" class="w-4 h-4 rounded accent-cyan-500">
            <span class="font-medium text-sm flex-1" :class="isEnabled(s.id) ? 'text-cyan-300' : 'text-white/40'">{{ s.name }}</span>
            <span class="text-xs text-white/50">{{ s.tools.length }} tools</span>
            <select v-if="isEnabled(s.id)" :value="getEnv(s.id)" @change="setEnv(s.id, $event.target.value)" @click.stop
              class="bg-ocean-700 border border-white/15 rounded px-2 py-0.5 text-xs text-white">
              <option value="local">local</option>
              <option value="beta">beta</option>
              <option value="prod">prod</option>
            </select>
            <span class="text-xs text-white/30">{{ expanded[s.id] ? '▼' : '▶' }}</span>
          </div>
          <!-- Tools -->
          <div v-if="expanded[s.id] && isEnabled(s.id)" class="px-4 pb-3 border-t border-white/5">
            <div class="flex items-center gap-2 py-2 mb-1">
              <button @click="selectAll(s.id)" class="text-[10px] px-2 py-0.5 rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30">全選</button>
              <button @click="deselectAll(s.id)" class="text-[10px] px-2 py-0.5 rounded bg-white/10 text-white/60 hover:bg-white/15">全不選</button>
              <span class="text-[10px] text-white/40 ml-auto">{{ getEnabledTools(s.id).length }}/{{ s.tools.length }}</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
              <label v-for="tool in s.tools" :key="tool" class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer text-xs">
                <input type="checkbox" :checked="isToolEnabled(s.id, tool)" @change="toggleTool(s.id, tool)" class="w-3.5 h-3.5 rounded accent-cyan-500">
                <span class="truncate" :class="isToolEnabled(s.id, tool) ? 'text-white/90' : 'text-white/40'">{{ tool }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AgentDetailLayout>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useAgentList } from '../composables/useAgentList.js'
import { useApi } from '../composables/useApi.js'
import AgentDetailLayout from '../components/AgentDetailLayout.vue'

const { get, post } = useApi()
const { agents, selectedAgent, loading, selectAgent } = useAgentList()

const poolLoading = ref(false)
const saving = ref(false)
const status = ref(null)
const expanded = reactive({})

// Pool data from MySQL
const poolServers = ref([])
// Agent config: { server_id: { env, enabled } }
const agentConfig = reactive({})
// Tool filter: { server_id: [tool_names] }  — empty = all tools
const toolFilter = reactive({})

async function onSelect(a) {
  selectAgent(a)
  await loadPool()
}

async function loadPool() {
  if (!selectedAgent.value) return
  poolLoading.value = true
  status.value = null
  const res = await get(`/api/mcp-servers/pool-for-agent/${selectedAgent.value.name}`)
  if (res) {
    poolServers.value = res.servers || []
    // Populate agentConfig
    Object.keys(agentConfig).forEach(k => delete agentConfig[k])
    for (const [sid, cfg] of Object.entries(res.agent_config || {})) {
      agentConfig[sid] = { env: cfg.env, enabled: cfg.enabled }
    }
    // Populate toolFilter
    Object.keys(toolFilter).forEach(k => delete toolFilter[k])
    for (const [sid, tools] of Object.entries(res.tool_filter || {})) {
      toolFilter[sid] = [...tools]
    }
  }
  poolLoading.value = false
}

watch(selectedAgent, (a) => { if (a) loadPool() })

// ─── Server helpers ───
function isEnabled(sid) { return agentConfig[sid]?.enabled ?? false }

function toggleServer(sid) {
  if (agentConfig[sid]) {
    agentConfig[sid].enabled = !agentConfig[sid].enabled
  } else {
    agentConfig[sid] = { env: 'local', enabled: true }
  }
}

function getEnv(sid) { return agentConfig[sid]?.env || 'local' }
function setEnv(sid, env) {
  if (!agentConfig[sid]) agentConfig[sid] = { env, enabled: true }
  else agentConfig[sid].env = env
}

// ─── Tool helpers ───
function getServerTools(sid) { return poolServers.value.find(s => s.id === sid)?.tools || [] }

function isToolEnabled(sid, tool) {
  if (!toolFilter[sid] || toolFilter[sid].length === 0) return true // no filter = all
  return toolFilter[sid].includes(tool)
}

function getEnabledTools(sid) {
  const all = getServerTools(sid)
  if (!toolFilter[sid] || toolFilter[sid].length === 0) return all
  return toolFilter[sid]
}

function toggleTool(sid, tool) {
  const all = getServerTools(sid)
  if (!toolFilter[sid] || toolFilter[sid].length === 0) {
    // Currently all → deselect this one
    toolFilter[sid] = all.filter(t => t !== tool)
  } else {
    const idx = toolFilter[sid].indexOf(tool)
    if (idx >= 0) toolFilter[sid].splice(idx, 1)
    else toolFilter[sid].push(tool)
    // If all selected, clear filter
    if (toolFilter[sid].length >= all.length) delete toolFilter[sid]
  }
}

function selectAll(sid) { delete toolFilter[sid] }
function deselectAll(sid) { toolFilter[sid] = [] }

function toggleExpand(sid) { expanded[sid] = !expanded[sid] }

// ─── Save ───
async function save() {
  saving.value = true
  status.value = null
  // Build payload: only enabled servers
  const config = {}
  const filter = {}
  for (const [sid, cfg] of Object.entries(agentConfig)) {
    if (cfg.enabled) {
      config[sid] = { env: cfg.env, enabled: true }
      if (toolFilter[sid] && toolFilter[sid].length > 0 && toolFilter[sid].length < getServerTools(parseInt(sid)).length) {
        filter[sid] = toolFilter[sid]
      }
    }
  }
  const res = await post(`/api/mcp-servers/save-agent-config/${selectedAgent.value.name}`, { config, toolFilter: filter })
  status.value = res?.ok ? { ok: true, text: '✅ 已儲存' } : { ok: false, text: '❌ ' + (res?.detail || '儲存失敗') }
  saving.value = false
}
</script>
