<template>
  <StatusBar :lastUpdate="lastUpdate" :countdown="countdown">
    <span>時間範圍：</span>
    <select v-model="hours" @change="loadAll()" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm">
      <option value="1">最近 1 小時</option>
      <option value="6">最近 6 小時</option>
      <option value="24">最近 24 小時</option>
      <option value="168">最近 7 天</option>
      <option value="720">最近 30 天</option>
    </select>
    <button @click="loadAll()" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </StatusBar>

  <div class="p-7">
    <!-- Total -->
    <div class="mb-6">
      <div class="flex items-center gap-3 mb-3">
        <span class="font-semibold">📊 全體加總</span>
        <span class="ml-auto text-sm bg-ocean-700 px-3 py-1 rounded">💻 {{ totalCpu }} &nbsp; 🧠 {{ totalMem }}</span>
      </div>
      <div class="flex gap-3">
        <div class="glass rounded-lg p-3 flex-1 min-w-0 cursor-pointer hover:shadow-lg hover:-translate-y-0.5 transition" @click="expand('_total', 'cpu', '全體加總')">
          <div class="text-xs text-white/70 mb-1">💻 CPU</div>
          <div class="h-24"><canvas ref="cpuTotal"></canvas></div>
        </div>
        <div class="glass rounded-lg p-3 flex-1 min-w-0 cursor-pointer hover:shadow-lg hover:-translate-y-0.5 transition" @click="expand('_total', 'mem', '全體加總')">
          <div class="text-xs text-white/70 mb-1">🧠 記憶體</div>
          <div class="h-24"><canvas ref="memTotal"></canvas></div>
        </div>
      </div>
    </div>

    <!-- Per Agent -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <div v-for="agent in sortedAgents" :key="agent.name" :id="'section-' + agent.name">
        <div class="flex items-center gap-3 mb-2">
          <img :src="'/avatar/' + agent.name" class="w-8 h-8 rounded-full object-cover border border-white/20" @error="$event.target.style.display='none'">
          <span class="font-semibold text-sm">{{ agent.display }}</span>
          <span class="ml-auto text-xs bg-ocean-700 px-2 py-0.5 rounded">{{ agent.stats }}</span>
        </div>
        <div class="flex gap-3">
          <div class="glass rounded-lg p-3 flex-1 min-w-0 cursor-pointer hover:shadow-lg transition" @click="expand(agent.name, 'cpu', agent.display)">
            <div class="text-xs text-white/70 mb-1">💻 CPU</div>
            <div class="h-24"><canvas :ref="el => setRef('cpu-' + agent.name, el)"></canvas></div>
          </div>
          <div class="glass rounded-lg p-3 flex-1 min-w-0 cursor-pointer hover:shadow-lg transition" @click="expand(agent.name, 'mem', agent.display)">
            <div class="text-xs text-white/70 mb-1">🧠 記憶體</div>
            <div class="h-24"><canvas :ref="el => setRef('mem-' + agent.name, el)"></canvas></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Expand Dialog -->
  <div v-if="dialog" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="dialog = null">
    <div class="bg-ocean-700 rounded-xl w-[95%] max-w-[1100px] flex flex-col shadow-2xl">
      <div class="px-6 py-4 border-b border-white/10 flex items-center gap-3 font-semibold">
        <img v-if="dialog.key !== '_total'" :src="'/avatar/' + dialog.key" class="w-8 h-8 rounded-full object-cover border border-white/20" @error="$event.target.style.display='none'">
        <span>{{ dialog.title }}</span>
        <span v-if="dialog.stats" class="text-sm font-normal text-white/70 bg-ocean-800 px-3 py-1 rounded">{{ dialog.stats }}</span>
        <button @click="dialog = null" class="ml-auto text-2xl text-white/60 hover:text-white">&times;</button>
      </div>
      <div class="px-6 py-5 flex gap-6">
        <div class="flex-1">
          <div class="text-sm text-white/70 mb-2">💻 CPU 用量 (%)</div>
          <div class="h-[300px]"><canvas ref="dialogCpuCanvas"></canvas></div>
        </div>
        <div class="flex-1">
          <div class="text-sm text-white/70 mb-2">🧠 記憶體用量</div>
          <div class="h-[300px]"><canvas ref="dialogMemCanvas"></canvas></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, inject } from 'vue'
import Chart from 'chart.js/auto'
import StatusBar from '../components/StatusBar.vue'
import { useApi } from '../composables/useApi.js'

const { get, formatMem, pad, formatTime24, parseCpuRaw, parseMemRaw } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const hours = ref('6')
const sortedAgents = ref([])
const totalCpu = ref('-')
const totalMem = ref('-')
const lastUpdate = ref('')
const countdown = ref(60)
const dialog = ref(null)

const cpuTotal = ref(null)
const memTotal = ref(null)
const dialogCpuCanvas = ref(null)
const dialogMemCanvas = ref(null)
const canvasRefs = {}
const charts = {}
let dialogCpuChart = null
let dialogMemChart = null

function setRef(key, el) { if (el) canvasRefs[key] = el }

async function loadAll() {
  let metrics = {}
  try { const r = await get('/api/metrics'); metrics = r?.metrics || {} } catch {}

  const gData = await get(`/api/agents?group=${currentGroup.value}`)
  const groupNames = (gData?.agents || []).map(a => a.name)

  let tc = 0, tm = 0
  const allAgents = (await get('/api/status'))?.agents || []
  const items = allAgents.filter(a => groupNames.includes(a.name)).map(a => {
    const m = metrics[a.deployment || a.name]; let cpu = 0, mem = 0
    if (m) { cpu = parseCpuRaw(m.cpu_raw); mem = parseMemRaw(m.memory_raw); tc += cpu; tm += mem }
    return { ...a, _mem: mem, stats: `💻 ${(cpu/10).toFixed(1)}%  🧠 ${formatMem(mem)}` }
  })

  items.sort((a, b) => b._mem - a._mem)
  sortedAgents.value = items
  totalCpu.value = (tc / 10).toFixed(1) + '%'
  totalMem.value = formatMem(tm)

  await nextTick()
  // Total history: pass comma-separated deployment names for group filtering
  const deployNames = items.map(a => a.deployment || a.name).join(',')
  await loadHistory('_total', deployNames, cpuTotal.value, memTotal.value)
  for (const a of items) {
    await loadHistory(a.name, a.deployment || a.name, canvasRefs['cpu-' + a.name], canvasRefs['mem-' + a.name])
  }
  lastUpdate.value = `最後更新：${formatTime24(new Date())}`
  countdown.value = 60
}

async function loadHistory(key, agentName, cpuCanvas, memCanvas) {
  const json = await get(`/api/metrics/history?hours=${hours.value}&agent=${agentName}`)
  const data = json?.data || []
  const labels = data.map(d => fmtLabel(d.ts))
  renderSmall(`cpu-${key}`, cpuCanvas, labels, data.map(d => d.cpu_pct), '#4fc3f7', '%')
  renderSmall(`mem-${key}`, memCanvas, labels, data.map(d => d.memory_mb), '#ce93d8', 'MB')
}

function renderSmall(id, canvas, labels, data, color, unit) {
  if (!canvas) return
  if (charts[id]) charts[id].destroy()
  const yFn = unit === '%' ? v => v + '%' : v => v >= 1024 ? (v/1024).toFixed(1) + 'G' : v + 'M'
  charts[id] = new Chart(canvas, {
    type: 'line',
    data: { labels, datasets: [{ data, borderColor: color, backgroundColor: color + '22', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 1.5 }] },
    options: { responsive: true, maintainAspectRatio: false, animation: false,
      scales: { x: { ticks: { color: '#bbb', font: { size: 9 }, maxTicksLimit: 4, maxRotation: 0 }, grid: { display: false } },
               y: { beginAtZero: true, ticks: { color: '#bbb', font: { size: 9 }, maxTicksLimit: 3, callback: yFn }, grid: { color: 'rgba(255,255,255,0.05)' } } },
      plugins: { legend: { display: false }, tooltip: { enabled: false } } }
  })
}

async function expand(key, type, name) {
  dialog.value = { title: name, key, stats: '' }
  await nextTick()
  const agentName = key === '_total' ? '' : key
  const json = await get(`/api/metrics/history?hours=${hours.value}&agent=${agentName}`)
  const data = json?.data || []

  // Show current stats from the latest data point
  if (data.length > 0) {
    const last = data[data.length - 1]
    const cpuStr = last.cpu_pct.toFixed(1) + '%'
    const memStr = last.memory_mb >= 1024 ? (last.memory_mb / 1024).toFixed(1) + ' GB' : last.memory_mb.toFixed(0) + ' MB'
    dialog.value.stats = `💻 ${cpuStr}  🧠 ${memStr}`
  }
  const labels = data.map(d => fmtLabel(d.ts))
  const cpuValues = data.map(d => d.cpu_pct)
  const memValues = data.map(d => d.memory_mb)

  if (dialogCpuChart) dialogCpuChart.destroy()
  if (dialogMemChart) dialogMemChart.destroy()

  const baseOpts = { responsive: true, maintainAspectRatio: false, animation: { duration: 300 }, interaction: { intersect: false, mode: 'index' },
    plugins: { legend: { display: false }, tooltip: { backgroundColor: 'rgba(10,22,40,0.9)', titleColor: '#90caf9', bodyColor: '#fff' } } }

  dialogCpuChart = new Chart(dialogCpuCanvas.value, {
    type: 'line',
    data: { labels, datasets: [{ data: cpuValues, borderColor: '#4fc3f7', backgroundColor: '#4fc3f722', fill: true, tension: 0.3, pointRadius: 2, borderWidth: 2 }] },
    options: { ...baseOpts, scales: {
      x: { ticks: { color: '#ccc', font: { size: 11 }, maxTicksLimit: 8, maxRotation: 0 }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { beginAtZero: true, ticks: { color: '#ccc', font: { size: 11 }, callback: v => v + '%' }, grid: { color: 'rgba(255,255,255,0.08)' } } } }
  })

  dialogMemChart = new Chart(dialogMemCanvas.value, {
    type: 'line',
    data: { labels, datasets: [{ data: memValues, borderColor: '#ce93d8', backgroundColor: '#ce93d822', fill: true, tension: 0.3, pointRadius: 2, borderWidth: 2 }] },
    options: { ...baseOpts, scales: {
      x: { ticks: { color: '#ccc', font: { size: 11 }, maxTicksLimit: 8, maxRotation: 0 }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { beginAtZero: true, ticks: { color: '#ccc', font: { size: 11 }, callback: v => v >= 1024 ? (v/1024).toFixed(1)+' GB' : v+' MB' }, grid: { color: 'rgba(255,255,255,0.08)' } } } }
  })
}

function fmtLabel(ts) {
  const dt = new Date(ts + 'Z'); const h = parseInt(hours.value)
  if (h <= 1) return `${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`
  if (h <= 24) return `${pad(dt.getHours())}:${pad(dt.getMinutes())}`
  return `${dt.getMonth()+1}/${dt.getDate()} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

let timer
onMounted(() => {
  loadAll()
  timer = setInterval(() => { countdown.value--; if (countdown.value <= 0) loadAll() }, 1000)
  window.addEventListener('group-changed', loadAll)
  const hash = location.hash.replace('#', '')
  if (hash) {
    setTimeout(() => {
      document.getElementById('section-' + hash)?.scrollIntoView({ behavior: 'smooth' })
      // Auto-open dialog for the agent
      const agent = sortedAgents.value.find(a => a.name === hash)
      if (agent) expand(agent.name, 'cpu', agent.display)
    }, 800)
  }
})
onUnmounted(() => clearInterval(timer))
</script>
