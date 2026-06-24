<template>
  <AgentDetailLayout :agents="agents" :selected-agent="selectedAgent" :loading="loading" @select="onSelect" @back="selectedAgent = null">
    <div v-if="!selectedAgent" class="text-center py-20 text-white/50 hidden md:block">
      <div class="text-3xl mb-2">🔌</div>
      <div>請選擇角色管理 MCP 配置</div>
    </div>

    <template v-if="selectedAgent">
      <div class="flex items-center gap-3 mb-5 flex-wrap">
        <h2 class="text-lg font-semibold">{{ selectedAgent.display }} — MCP 配置</h2>
        <button @click="save()" :disabled="saving" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-50">
          {{ saving ? '儲存中...' : '💾 儲存 & 生成 mcp.json' }}
        </button>
      </div>

      <div v-if="status" class="mb-4 px-4 py-2 rounded-lg text-sm" :class="status.ok ? 'bg-green-500/15 text-green-300' : 'bg-red-500/15 text-red-300'">{{ status.text }}</div>

      <div v-if="poolLoading" class="text-white/50 text-sm py-4">載入中...</div>
      <div v-else-if="!poolServers.length" class="text-center py-10 text-white/50">
        <div class="text-2xl mb-2">📭</div>
        <div>尚無 MCP Server，請先到 <a href="/mcp-servers" class="text-cyan-400 underline">MCP Servers</a> 頁面新增</div>
      </div>
      <div v-else class="space-y-2">
        <div v-for="s in poolServers" :key="s.id" class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
          <div class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/5" @click="toggleExpand(s.id)">
            <input type="checkbox" :checked="isEnabled(s.id)" @click.stop="toggleServer(s.id)" class="w-4 h-4 rounded accent-cyan-500">
            <span class="text-lg">{{ s.type === 'remote' ? '🌐' : '💻' }}</span>
            <span class="font-medium text-sm flex-1" :class="isEnabled(s.id) ? 'text-cyan-300' : 'text-white/40'">{{ s.name }}</span>
            <span class="text-[10px] px-2 py-0.5 rounded bg-ocean-700 text-white/50">{{ s.type }}</span>
            <span v-if="s.auto_approve.length" class="text-xs text-white/40">{{ s.auto_approve.length }} tools</span>
            <span class="text-xs text-white/30">{{ expanded[s.id] ? '▼' : '▶' }}</span>
          </div>

          <!-- Expanded: show auto_approve tools -->
          <div v-if="expanded[s.id] && isEnabled(s.id) && s.auto_approve.length" class="px-4 pb-3 border-t border-white/5">
            <div class="py-2 text-[10px] text-white/50 uppercase">Auto Approve Tools</div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="t in s.auto_approve" :key="t" class="text-xs bg-ocean-700 px-2 py-1 rounded text-white/80">{{ t }}</span>
            </div>
          </div>
          <div v-if="expanded[s.id] && isEnabled(s.id) && !s.auto_approve.length" class="px-4 pb-3 border-t border-white/5">
            <div class="py-2 text-xs text-white/40">此 server 未定義 autoApprove tools</div>
          </div>
        </div>
      </div>
    </template>
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
const poolServers = ref([])
const agentConfig = reactive({}) // {server_id: {enabled}}

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
    Object.keys(agentConfig).forEach(k => delete agentConfig[k])
    for (const [sid, cfg] of Object.entries(res.agent_config || {})) {
      agentConfig[sid] = { enabled: cfg.enabled }
    }
  }
  poolLoading.value = false
}

watch(selectedAgent, (a) => { if (a) loadPool() })

function isEnabled(sid) { return agentConfig[sid]?.enabled ?? false }

function toggleServer(sid) {
  if (agentConfig[sid]) {
    agentConfig[sid].enabled = !agentConfig[sid].enabled
  } else {
    agentConfig[sid] = { enabled: true }
  }
}

function toggleExpand(sid) { expanded[sid] = !expanded[sid] }

async function save() {
  saving.value = true
  status.value = null
  const config = {}
  for (const [sid, cfg] of Object.entries(agentConfig)) {
    if (cfg.enabled) {
      config[sid] = { enabled: true }
    }
  }
  const res = await post(`/api/mcp-servers/save-agent-config/${selectedAgent.value.name}`, { config })
  status.value = res?.ok ? { ok: true, text: '✅ 已儲存並生成 mcp.json' } : { ok: false, text: '❌ ' + (res?.detail || '儲存失敗') }
  saving.value = false
}
</script>
