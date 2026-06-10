<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">討論串分析</span>
    <button @click="load()" class="ml-auto bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </div>

  <div class="p-7">
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-4"></div>
      <span class="text-white/60 text-sm">統計中...</span>
    </div>
    <div v-else-if="!data" class="text-center py-12 text-white/50">載入中...</div>
    <template v-else>
      <!-- Summary -->
      <div class="grid grid-cols-2 gap-4 mb-6">
        <div class="glass rounded-xl p-4 text-center">
          <div class="text-2xl font-bold text-cyan-300">{{ data.total_threads }}</div>
          <div class="text-xs text-white/50 mt-1">活躍討論串（未封存）</div>
        </div>
        <div class="glass rounded-xl p-4 text-center">
          <div class="text-2xl font-bold text-cyan-300">{{ totalMessages }}</div>
          <div class="text-xs text-white/50 mt-1">總訊息數</div>
        </div>
      </div>

      <!-- Daily Post Chart -->
      <div class="glass rounded-xl p-5 mb-6" v-show="data.daily_chart && data.daily_chart.length">
        <h3 class="font-semibold mb-3 text-cyan-300">📈 每日新增討論串</h3>
        <div class="h-48"><canvas :ref="el => { chartEl = el; if(el) renderChart() }"></canvas></div>
      </div>

      <!-- Top Threads -->
      <div v-if="data.top_threads && data.top_threads.length" class="glass rounded-xl overflow-hidden">
        <h3 class="font-semibold px-5 pt-4 pb-2 text-cyan-300">🔥 熱門討論串（點擊查看對話分析）</h3>
        <table class="w-full">
          <thead><tr class="bg-ocean-800/60">
            <th class="text-left px-5 py-2 text-sm font-semibold">討論串</th>
            <th class="text-left px-5 py-2 text-sm font-semibold">頻道</th>
            <th class="text-left px-5 py-2 text-sm font-semibold">標籤</th>
            <th class="text-right px-5 py-2 text-sm font-semibold">訊息</th>
            <th class="text-right px-5 py-2 text-sm font-semibold">最後對話</th>
          </tr></thead>
          <tbody>
            <tr v-for="t in data.top_threads" :key="t.id" class="border-t border-white/5 hover:bg-white/5 cursor-pointer" @click="openDetail(t)">
              <td class="px-5 py-2 text-sm font-medium truncate max-w-[250px]">{{ t.name }}</td>
              <td class="px-5 py-2 text-sm text-white/60">#{{ t.parent }}</td>
              <td class="px-5 py-2 text-sm">
                <div class="flex flex-wrap gap-1">
                  <span v-for="tag in t.tags" :key="tag" class="text-xs px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">{{ tag }}</span>
                </div>
              </td>
              <td class="px-5 py-2 text-sm text-right font-medium">{{ t.message_count }}</td>
              <td class="px-5 py-2 text-sm text-right text-white/50">{{ t.last_activity ? t.last_activity.slice(5) : '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Thread Detail Dialog -->
    <div v-if="detail" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="detail = null">
      <div class="bg-ocean-700 rounded-xl w-[92%] max-w-[900px] flex flex-col shadow-2xl max-h-[85vh]">
        <div class="px-6 py-4 border-b border-white/10 flex items-center gap-3 font-semibold shrink-0">
          <span>📊 {{ detail.name }}</span>
          <span class="text-sm font-normal text-white/50">{{ detail.message_count }} 則訊息</span>
          <button @click="detail = null" class="ml-auto text-2xl text-white/60 hover:text-white">&times;</button>
        </div>
        <div class="px-6 py-5 overflow-y-auto">
          <div v-if="detailLoading" class="flex items-center justify-center py-12">
            <div class="w-8 h-8 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
          </div>
          <div v-show="!detailLoading">
            <div class="h-[250px] mb-4"><canvas ref="detailChartEl"></canvas></div>
            <p class="text-xs text-white/40 text-center mb-6">對話密度（每小時訊息數）</p>
            <div class="flex gap-4">
              <div v-if="autoIndex" class="glass rounded-lg p-4 w-48 text-center shrink-0">
                <div class="text-3xl font-bold" :class="autoIndex.score >= 70 ? 'text-green-400' : autoIndex.score >= 40 ? 'text-yellow-400' : 'text-red-400'">{{ autoIndex.score }}%</div>
                <div class="text-xs text-white/50 mt-1">自動化指數</div>
                <div class="text-xs text-white/40 mt-2">🤖 {{ autoIndex.botMsgs }} / 👤 {{ autoIndex.humanMsgs }}</div>
              </div>
              <div v-if="authorStats.length" class="flex-1">
                <h4 class="text-sm font-semibold text-cyan-300 mb-3">👥 參與者</h4>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                  <div v-for="a in authorStats" :key="a.name" class="flex items-center gap-2 bg-ocean-800/50 rounded px-3 py-2">
                    <img v-if="a.avatar" :src="a.avatar" class="w-5 h-5 rounded-full">
                    <div v-else class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" :class="a.is_bot ? 'bg-purple-700' : 'bg-cyan-700'">{{ a.is_bot ? '🤖' : a.name.charAt(0) }}</div>
                    <span class="text-sm flex-1 truncate">{{ a.name }}</span>
                    <span class="text-xs text-white/60">{{ a.count }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, inject } from 'vue'
import Chart from 'chart.js/auto'
import { useApi } from '../composables/useApi.js'

const { get } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const loading = ref(false)
const data = ref(null)
const chartEl = ref(null)
const detail = ref(null)
const detailLoading = ref(false)
const detailChartEl = ref(null)
const detailMessages = ref([])
let chartInstance = null
let detailChartInstance = null

const totalMessages = computed(() => data.value?.top_threads?.reduce((s, t) => s + t.message_count, 0) || 0)

const authorStats = computed(() => {
  if (!detailMessages.value.length) return []
  const counts = {}
  detailMessages.value.forEach(m => {
    const name = m.author || 'unknown'
    if (!counts[name]) counts[name] = { count: 0, is_bot: m.is_bot, avatar: m.avatar }
    counts[name].count++
  })
  return Object.entries(counts).map(([name, d]) => ({ name, count: d.count, is_bot: d.is_bot, avatar: d.avatar })).sort((a, b) => b.count - a.count)
})

const autoIndex = computed(() => {
  if (!detailMessages.value.length) return null
  const bot = detailMessages.value.filter(m => m.is_bot).length
  const total = detailMessages.value.length
  return { score: Math.round(bot / total * 100), botMsgs: bot, humanMsgs: total - bot }
})

async function load() {
  loading.value = true
  try { data.value = await get(`/api/discord/activity?group=${currentGroup.value}`) } catch (e) { console.error(e) }
  loading.value = false
}

function renderChart() {
  if (!data.value?.daily_chart?.length || !chartEl.value) return
  if (chartInstance) chartInstance.destroy()
  const days = data.value.daily_chart
  const filled = []
  if (days.length >= 2) {
    const start = new Date(days[0].date), end = new Date(days[days.length - 1].date)
    const map = Object.fromEntries(days.map(d => [d.date, d.count]))
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const k = d.toISOString().slice(0, 10)
      filled.push({ date: k, count: map[k] || 0 })
    }
  } else filled.push(...days)

  chartInstance = new Chart(chartEl.value, {
    type: 'line',
    data: { labels: filled.map(d => d.date.slice(5)), datasets: [{ data: filled.map(d => d.count), borderColor: '#4fc3f7', backgroundColor: '#4fc3f722', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 }] },
    options: { responsive: true, maintainAspectRatio: false, animation: false,
      interaction: { intersect: false, mode: 'index' },
      scales: { x: { ticks: { color: '#bbb', font: { size: 10 }, maxRotation: 0, maxTicksLimit: 15 }, grid: { display: false } }, y: { beginAtZero: true, ticks: { color: '#bbb', font: { size: 10 }, stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } } },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.parsed.y + ' 則貼文' } } } }
  })
}

async function openDetail(t) {
  detail.value = t
  detailLoading.value = true
  detailMessages.value = []
  try {
    const res = await get(`/api/discord/threads/${t.id}/messages?mode=all`)
    detailMessages.value = res?.messages || []
  } catch (e) { console.error(e) }
  detailLoading.value = false
}

function renderDetailChart() {
  if (!detailChartEl.value || !detailMessages.value.length) return
  if (detailChartInstance) detailChartInstance.destroy()
  const timestamps = detailMessages.value.map(m => new Date(m.timestamp).getTime()).sort((a, b) => a - b)
  const hourMs = 60 * 60 * 1000
  const start = Math.floor(timestamps[0] / hourMs) * hourMs
  const end = Math.floor(timestamps[timestamps.length - 1] / hourMs) * hourMs
  const buckets = {}
  for (let t = start; t <= end; t += hourMs) buckets[t] = 0
  timestamps.forEach(ts => { buckets[Math.floor(ts / hourMs) * hourMs]++ })
  const sorted = Object.entries(buckets).sort((a, b) => a[0] - b[0])
  const labels = sorted.map(([k]) => { const d = new Date(parseInt(k)); return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:00` })
  detailChartInstance = new Chart(detailChartEl.value, {
    type: 'line',
    data: { labels, datasets: [{ data: sorted.map(([,v]) => v), borderColor: '#4fc3f7', backgroundColor: '#4fc3f722', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 1.5 }] },
    options: { responsive: true, maintainAspectRatio: false, animation: false,
      interaction: { intersect: false, mode: 'index' },
      scales: { x: { ticks: { color: '#bbb', font: { size: 9 }, maxRotation: 0, maxTicksLimit: 12 }, grid: { display: false } }, y: { beginAtZero: true, ticks: { color: '#bbb', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } } },
      plugins: { legend: { display: false }, tooltip: { enabled: true, callbacks: { label: ctx => ctx.parsed.y + ' 則訊息' } } } }
  })
}

watch(detailMessages, async (msgs) => {
  if (msgs.length) { await nextTick(); setTimeout(renderDetailChart, 200) }
})

onMounted(() => {
  load()
  window.addEventListener('group-changed', load)
})
</script>
