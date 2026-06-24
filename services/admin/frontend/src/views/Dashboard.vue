<template>
  <StatusBar :lastUpdate="lastUpdate" :countdown="countdown">
    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-green-500"></span>{{ running }} 運行中</div>
    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-red-500"></span>{{ down }} 停止</div>
    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-gray-400"></span>{{ agents.length }} 總計</div>
    <router-link to="/metrics" title="全體 CPU 用量" class="hover:text-cyan-400 transition cursor-pointer">💻 {{ totalCpu }}</router-link>
    <router-link to="/metrics" title="全體記憶體用量" class="hover:text-cyan-400 transition cursor-pointer">🧠 {{ totalMem }}</router-link>
  </StatusBar>

  <!-- Alert Banner -->
  <div v-if="alerts.length" class="border-b border-white/10">
    <div v-for="a in alerts" :key="a.id"
      :class="a.level === 'critical' ? 'bg-red-500/15 text-red-300' : 'bg-yellow-500/15 text-yellow-300'"
      class="flex items-center gap-4 px-7 py-2.5 text-sm border-b border-white/5">
      <span class="text-white/60 text-xs min-w-[50px]">{{ fmtTime(a.ts) }}</span>
      <span class="font-semibold min-w-[70px]">{{ a.agent }}</span>
      <span class="flex-1">{{ a.message }}</span>
      <button @click="dismissAlert(a.id)" class="border border-white/20 rounded px-2 py-0.5 text-xs text-white/70 hover:text-white hover:bg-white/10">✕</button>
    </div>
  </div>

  <!-- Agent Grid -->
  <div class="p-4 sm:p-7">
    <div v-if="!agents.length" class="text-center py-20 text-white/50">
      <div class="text-4xl mb-3">📭</div>
      <div>此伺服器尚未配置角色</div>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <div v-for="agent in sortedAgents" :key="agent.name"
        class="glass rounded-xl p-5 border-l-4 transition hover:-translate-y-0.5 hover:shadow-lg"
        :class="borderClass(agent.status)">
        <div class="flex items-center gap-3 mb-3">
          <img :src="'/avatar/' + agent.name" class="w-12 h-12 rounded-full object-cover border-2 border-white/20"
            @error="$event.target.style.display='none'">
          <div class="flex-1 min-w-0">
            <div class="font-semibold truncate">{{ agent.display }}</div>
            <div class="text-sm text-white/70 truncate" :title="agent.role">{{ agent.role }}</div>
          </div>
          <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="badgeClass(agent.status)">{{ statusLabel(agent.status) }}</span>
        </div>
        <div class="grid grid-cols-2 gap-1.5 text-sm mb-3">
          <div title="運行時間">⏱️ {{ agent.uptime || '-' }}</div>
          <div title="重啟次數">🔄 {{ agent.restarts ?? '-' }}</div>
          <div title="CPU 用量"><router-link :to="'/metrics#' + agent.name" class="hover:text-cyan-400 transition">💻 {{ agent.cpu || '-' }}</router-link></div>
          <div title="記憶體用量"><router-link :to="'/metrics#' + agent.name" class="hover:text-cyan-400 transition">🧠 {{ agent.memory || '-' }}</router-link></div>
        </div>
        <div class="flex gap-2">
          <button v-if="userRole === 'admin'" @click="restart(agent)" class="px-3 py-1.5 text-xs rounded border border-amber-400/30 text-amber-300 hover:bg-amber-400/10">🔁 重啟</button>
          <button @click="openLogs(agent)" class="px-3 py-1.5 text-xs rounded border border-cyan-400/30 text-cyan-300 hover:bg-cyan-400/10">📋 Log</button>
          <router-link v-if="userRole === 'admin'" :to="'/agent-config/' + (agent.bot_id || agent.name)" class="px-3 py-1.5 text-xs rounded border border-white/15 text-white/70 hover:bg-white/10 no-underline">⚙️ 設定</router-link>
        </div>
      </div>
    </div>
  </div>

  <!-- Log Modal -->
  <div v-if="logModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="logModal = false">
    <div class="bg-ocean-700 rounded-xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
      <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between font-semibold">
        <span>{{ logTitle }}</span>
        <button @click="logModal = false" class="text-2xl text-white/60 hover:text-white">&times;</button>
      </div>
      <div class="px-6 py-4 overflow-y-auto flex-1">
        <pre class="text-xs leading-relaxed whitespace-pre-wrap break-all text-white/90 bg-black/30 p-4 rounded-lg">{{ logContent }}</pre>
      </div>
    </div>
  </div>

  <!-- Toast -->
  <div v-if="toast" class="fixed bottom-6 right-6 px-5 py-3 rounded-lg text-sm z-50 shadow-lg"
    :class="toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'">{{ toast.msg }}</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, watch } from 'vue'
import StatusBar from '../components/StatusBar.vue'
import { useApi } from '../composables/useApi.js'

const { get, post, formatMem, pad, formatTime24, parseCpuRaw, parseMemRaw } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const agents = ref([])
const allAgents = ref([])
const groupAgentNames = ref([])
const alerts = ref([])
const running = ref(0)
const down = ref(0)
const totalCpu = ref('-')
const totalMem = ref('-')
const lastUpdate = ref('載入中...')
const countdown = ref(10)
const logModal = ref(false)
const logTitle = ref('')
const logContent = ref('')
const toast = ref(null)
const userRole = ref('viewer')

const sortedAgents = computed(() => [...agents.value].sort((a, b) => (b._memMb || 0) - (a._memMb || 0)))

async function fetchAll() {
  const [sData, mData, gData] = await Promise.all([get('/api/status'), get('/api/metrics'), get(`/api/agents?group=${currentGroup.value}`)])
  if (!sData || !mData) return
  groupAgentNames.value = (gData?.agents || []).map(a => a.name)
  const metrics = mData.metrics || {}
  let tc = 0, tm = 0, r = 0, d = 0
  const filtered = (sData.agents || []).filter(a => groupAgentNames.value.includes(a.name))
  agents.value = filtered.map(a => {
    const m = metrics[a.deployment || a.name]
    let cpuMilli = 0, memMb = 0
    if (m) {
      cpuMilli = parseCpuRaw(m.cpu_raw)
      memMb = parseMemRaw(m.memory_raw)
      tc += cpuMilli; tm += memMb
    }
    if (a.status === 'running') r++; else if (a.status !== 'unknown') d++
    return { ...a, cpu: m?.cpu || '-', memory: m?.memory || '-', _memMb: memMb }
  })
  running.value = r; down.value = d
  totalCpu.value = (tc / 10).toFixed(1) + '%'
  totalMem.value = formatMem(tm)
  lastUpdate.value = `最後更新：${formatTime24(new Date())}`
  countdown.value = 10
}

async function fetchAlerts() {
  const data = await get('/api/alerts')
  if (data) alerts.value = (data.alerts || []).filter(a => !groupAgentNames.value.length || groupAgentNames.value.includes(a.agent))
}

async function dismissAlert(id) {
  await post(`/api/alerts/${id}/dismiss`)
  fetchAlerts()
}

async function restart(agent) {
  if (!confirm(`確定要重啟 ${agent.display}？`)) return
  const data = await post(`/api/restart/${agent.name}`)
  showToast(data?.detail ? `❌ ${data.detail}` : `✅ ${agent.display} 已觸發重啟`, data?.detail ? 'error' : 'success')
  setTimeout(fetchAll, 3000)
}

async function openLogs(agent) {
  logModal.value = true
  logTitle.value = `📋 ${agent.display} — 最近 Log`
  logContent.value = '載入中...'
  const data = await get(`/api/logs/${agent.name}?lines=80`)
  logContent.value = data?.logs || '(無內容)'
}

function showToast(msg, type) {
  toast.value = { msg, type }
  setTimeout(() => { toast.value = null }, 3000)
}

function fmtTime(ts) {
  const dt = new Date(ts + 'Z')
  return `${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

function borderClass(s) {
  return { running: 'border-green-500', pending: 'border-yellow-500', failed: 'border-red-500', not_found: 'border-red-500', unknown: 'border-gray-500' }[s] || 'border-gray-500'
}
function badgeClass(s) {
  return { running: 'bg-green-500/20 text-green-300', pending: 'bg-yellow-500/20 text-yellow-300', failed: 'bg-red-500/20 text-red-300', not_found: 'bg-red-500/20 text-red-300', unknown: 'bg-gray-500/20 text-gray-300' }[s] || ''
}
function statusLabel(s) {
  return { running: '運行中', pending: '啟動中', failed: '失敗', not_found: '未部署', unknown: '未知' }[s] || s
}

let interval1, interval2, interval3
onMounted(async () => {
  fetchAll(); fetchAlerts()
  interval1 = setInterval(fetchAll, 10000)
  interval2 = setInterval(fetchAlerts, 30000)
  interval3 = setInterval(() => { countdown.value = Math.max(0, countdown.value - 1) }, 1000)
  try { const me = await get('/api/me'); if (me) userRole.value = me.role || 'viewer' } catch {}
  window.addEventListener('group-changed', () => { fetchAll(); fetchAlerts() })
})
onUnmounted(() => { clearInterval(interval1); clearInterval(interval2); clearInterval(interval3) })
</script>
