<template>
  <AgentDetailLayout :agents="agents" :selected-agent="selectedAgent" :loading="loading" @select="onSelect" @back="selectedAgent = null">
    <div v-if="!selectedAgent" class="text-center py-20 text-white/50 hidden md:block">
      <div class="text-3xl mb-2">🔌</div>
      <div>請選擇角色管理 MCP 配置</div>
    </div>

    <template v-if="selectedAgent">
      <!-- Header -->
      <div class="flex items-center gap-3 mb-5 flex-wrap">
        <h2 class="text-lg font-semibold">{{ selectedAgent.display }} — MCP Pool</h2>
        <div class="ml-auto flex gap-2">
          <button @click="save()" :disabled="saving" class="px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-50">
            {{ saving ? '儲存中...' : '💾 儲存 & 生成' }}
          </button>
        </div>
      </div>

      <div v-if="status" class="mb-4 px-4 py-2 rounded-lg text-sm" :class="status.ok ? 'bg-green-500/15 text-green-300' : 'bg-red-500/15 text-red-300'">{{ status.text }}</div>

      <!-- Basic settings -->
      <div class="flex gap-4 mb-5 flex-wrap">
        <div>
          <label class="block text-[10px] text-white/50 uppercase mb-1">Profile</label>
          <select v-model="agentCfg.profile" class="bg-ocean-800 border border-white/20 rounded px-3 py-1.5 text-sm text-white">
            <option v-for="p in profileNames" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div>
          <label class="block text-[10px] text-white/50 uppercase mb-1">預設環境</label>
          <select v-model="agentCfg.default" class="bg-ocean-800 border border-white/20 rounded px-3 py-1.5 text-sm text-white">
            <option v-for="e in envNames" :key="e" :value="e">{{ e }}</option>
          </select>
        </div>
      </div>

      <!-- Server list -->
      <div v-if="poolLoading" class="text-white/50 text-sm py-4">載入 Pool 中...</div>
      <div v-else class="space-y-2">
        <div v-for="name in allServerNames" :key="name"
          class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <!-- Server header -->
          <div class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/5"
            @click="toggleExpand(name)">
            <input type="checkbox" :checked="isServerEnabled(name)" @click.stop="toggleServer(name)"
              class="w-4 h-4 rounded accent-cyan-500">
            <span class="font-medium text-sm flex-1" :class="isServerEnabled(name) ? 'text-cyan-300' : 'text-white/40'">
              {{ name }}
            </span>
            <span class="text-xs text-white/50">{{ getServerTools(name).length }} tools</span>
            <select v-if="isServerEnabled(name)" :value="getServerEnv(name)" @change="setServerEnv(name, $event.target.value)"
              @click.stop class="bg-ocean-700 border border-white/15 rounded px-2 py-0.5 text-xs text-white">
              <option v-for="e in envNames" :key="e" :value="e">{{ e }}</option>
            </select>
            <span class="text-xs text-white/40">{{ expanded[name] ? '▼' : '▶' }}</span>
          </div>

          <!-- Tools (expanded) -->
          <div v-if="expanded[name] && isServerEnabled(name)" class="px-4 pb-3 border-t border-white/5">
            <div class="flex items-center gap-2 py-2 mb-1">
              <button @click="selectAllTools(name)" class="text-[10px] px-2 py-0.5 rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30">全選</button>
              <button @click="deselectAllTools(name)" class="text-[10px] px-2 py-0.5 rounded bg-white/10 text-white/60 hover:bg-white/15">全不選</button>
              <span class="text-[10px] text-white/40 ml-auto">{{ getEnabledToolCount(name) }}/{{ getServerTools(name).length }}</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
              <label v-for="tool in getServerTools(name)" :key="tool"
                class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer text-xs">
                <input type="checkbox" :checked="isToolEnabled(name, tool)" @change="toggleTool(name, tool)"
                  class="w-3.5 h-3.5 rounded accent-cyan-500">
                <span class="truncate" :class="isToolEnabled(name, tool) ? 'text-white/90' : 'text-white/40'">{{ tool }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </template>
  </AgentDetailLayout>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useAgentList } from '../composables/useAgentList.js'
import { useApi } from '../composables/useApi.js'
import AgentDetailLayout from '../components/AgentDetailLayout.vue'

const { get, post } = useApi()
const { agents, selectedAgent, loading, selectAgent } = useAgentList()

const poolLoading = ref(false)
const saving = ref(false)
const status = ref(null)
const expanded = reactive({})

// Pool data (global)
const pool = ref({ servers: {}, environments: [], profiles: {} })
const allServerNames = computed(() => Object.keys(pool.value.servers))
const envNames = computed(() => pool.value.environments.map(e => e.name))
const profileNames = computed(() => Object.keys(pool.value.profiles))

// Agent config (editable)
const agentCfg = reactive({
  profile: 'full',
  default: 'local',
  overrides: {},
  disabled: [],
  toolFilter: {}
})

async function loadPool() {
  poolLoading.value = true
  const res = await get('/api/mcp-pool')
  if (res) pool.value = res
  poolLoading.value = false
}

async function loadAgentConfig() {
  if (!selectedAgent.value) return
  const res = await get(`/api/mcp-pool/agent/${selectedAgent.value.name}`)
  if (res?.config) {
    const c = res.config
    agentCfg.profile = c.profile || 'full'
    agentCfg.default = c.default || 'local'
    agentCfg.overrides = c.overrides || {}
    agentCfg.disabled = c.disabled || []
    agentCfg.toolFilter = c.toolFilter || {}
  } else {
    agentCfg.profile = 'full'
    agentCfg.default = 'local'
    agentCfg.overrides = {}
    agentCfg.disabled = []
    agentCfg.toolFilter = {}
  }
  status.value = null
}

function onSelect(a) {
  selectAgent(a)
  loadAgentConfig()
}

// Load pool on mount
loadPool()
watch(selectedAgent, (a) => { if (a) loadAgentConfig() })

// ─── Server helpers ───
function isServerEnabled(name) {
  const profileServers = pool.value.profiles[agentCfg.profile] || []
  return profileServers.includes(name) && !agentCfg.disabled.includes(name)
}

function toggleServer(name) {
  const profileServers = pool.value.profiles[agentCfg.profile] || []
  if (!profileServers.includes(name)) return

  if (agentCfg.disabled.includes(name)) {
    agentCfg.disabled = agentCfg.disabled.filter(s => s !== name)
  } else {
    agentCfg.disabled.push(name)
    delete agentCfg.overrides[name]
    delete agentCfg.toolFilter[name]
  }
}

function getServerEnv(name) {
  return agentCfg.overrides[name] || agentCfg.default
}

function setServerEnv(name, env) {
  if (env === agentCfg.default) {
    delete agentCfg.overrides[name]
  } else {
    agentCfg.overrides[name] = env
  }
}

function getServerTools(name) {
  return pool.value.servers[name]?.autoApprove || []
}

// ─── Tool helpers ───
function isToolEnabled(server, tool) {
  if (!agentCfg.toolFilter[server]) return true
  return agentCfg.toolFilter[server].includes(tool)
}

function toggleTool(server, tool) {
  const allTools = getServerTools(server)
  if (!agentCfg.toolFilter[server]) {
    agentCfg.toolFilter[server] = allTools.filter(t => t !== tool)
  } else {
    const idx = agentCfg.toolFilter[server].indexOf(tool)
    if (idx >= 0) {
      agentCfg.toolFilter[server].splice(idx, 1)
    } else {
      agentCfg.toolFilter[server].push(tool)
    }
    if (agentCfg.toolFilter[server].length >= allTools.length) {
      delete agentCfg.toolFilter[server]
    }
  }
}

function selectAllTools(server) { delete agentCfg.toolFilter[server] }
function deselectAllTools(server) { agentCfg.toolFilter[server] = [] }

function getEnabledToolCount(server) {
  const all = getServerTools(server)
  if (!agentCfg.toolFilter[server]) return all.length
  return agentCfg.toolFilter[server].length
}

function toggleExpand(name) { expanded[name] = !expanded[name] }

// ─── Save ───
async function save() {
  saving.value = true
  status.value = null

  const cleanFilter = {}
  for (const [k, v] of Object.entries(agentCfg.toolFilter)) {
    if (v && v.length > 0 && v.length < getServerTools(k).length) {
      cleanFilter[k] = v
    }
  }

  const payload = {
    profile: agentCfg.profile,
    default: agentCfg.default,
    overrides: { ...agentCfg.overrides },
    disabled: agentCfg.disabled.length ? agentCfg.disabled : undefined,
    toolFilter: Object.keys(cleanFilter).length ? cleanFilter : undefined,
  }

  const res = await post(`/api/mcp-pool/agent/${selectedAgent.value.name}`, payload)
  if (res?.ok) {
    status.value = { ok: true, text: `✅ ${res.message}` }
    if (res.generate?.error) {
      status.value.text += ` （⚠️ generate: ${res.generate.error}）`
    }
  } else {
    status.value = { ok: false, text: '❌ ' + (res?.detail || '儲存失敗') }
  }
  saving.value = false
}
</script>
