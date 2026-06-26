<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span>時間範圍：</span>
    <select v-model="range" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm">
      <option value="7d">近 7 天</option>
      <option value="week:2">近 14 天</option>
      <option value="1">本月</option>
      <option value="2">近 2 個月</option>
      <option value="3">近 3 個月</option>
    </select>
    <button @click="loadAll(true)" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
    <span v-if="cacheTime" class="ml-auto text-white/50 text-xs">快取時間：{{ cacheTime }}</span>
  </div>

  <div class="p-7 space-y-8">
    <div class="flex gap-1 bg-ocean-800/50 rounded-lg p-1 w-fit">
      <button v-for="t in tabs" :key="t.key" @click="switchTab(t.key)"
        :class="activeTab === t.key ? 'bg-cyan-600 text-white' : 'text-white/60 hover:text-white'"
        class="px-4 py-2 rounded-md text-sm font-medium transition">{{ t.label }}</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-4"></div>
      <span class="text-white/60 text-sm">查詢中，請稍候...</span>
    </div>

    <!-- Kiro Usage Tab -->
    <div v-if="!loading && activeTab === 'usage'" class="space-y-6">
      <div v-if="!usageData" class="text-center py-12 text-white/50">尚無資料，請點擊「更新」查詢</div>
      <template v-else>
        <!-- Summary Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-cyan-300">{{ kiroTotalUsed }}</div>
            <div class="text-xs text-white/50 mt-1">團隊總消耗</div>
          </div>
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-cyan-300">{{ kiroDailyAvg }}</div>
            <div class="text-xs text-white/50 mt-1">日均消耗 <span class="text-white/30">(排除低用量日)</span></div>
          </div>
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-purple-300">{{ kiroTopUser }}</div>
            <div class="text-xs text-white/50 mt-1">最活躍使用者</div>
          </div>
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-purple-300">{{ kiroRemainDays }}</div>
            <div class="text-xs text-white/50 mt-1">剩餘天數預估</div>
          </div>
        </div>

        <!-- Daily Usage Chart (stacked bar + total line) -->
        <div v-if="kiroDailyData.length" class="glass rounded-xl p-5">
          <h3 class="font-semibold mb-3 text-cyan-300">📊 每日用量</h3>
          <div class="h-72"><canvas ref="kiroStackedChart"></canvas></div>
        </div>

        <!-- Usage Ranking (Progress Bars) -->
        <div v-for="period in usageData.periods" :key="period.label" class="glass rounded-xl p-5">
          <h3 class="font-semibold mb-4 text-cyan-300">📊 額度排名 — {{ period.label }}</h3>
          <div class="space-y-3">
            <div v-for="(u, i) in period.users" :key="u.user" class="flex items-center gap-4">
              <span class="w-6 text-center text-lg">{{ medals[i] || '' }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-medium">{{ u.user }}</span>
                  <span class="text-xs text-white/50">{{ u.tier }}</span>
                  <span class="text-xs text-white/40 ml-auto">{{ u.pct.toFixed(0) }}%</span>
                </div>
                <div class="flex items-center gap-3">
                  <div class="flex-1 h-2.5 bg-ocean-800 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all" :class="barColor(u.pct)" :style="{width: Math.min(u.pct, 100) + '%'}"></div>
                  </div>
                  <span class="text-xs text-white/70 min-w-[90px] text-right">{{ u.credits.toFixed(1) }} / {{ u.limit }}</span>
                </div>
              </div>
              <div class="text-xs text-white/50 min-w-[130px] text-right">
                <span title="訊息數">💬 {{ u.messages }}</span>
                <span class="ml-2" title="對話數">🗂️ {{ u.conversations }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Daily Detail Table -->
        <div v-if="kiroDailyData.length" class="glass rounded-xl overflow-hidden">
          <h3 class="font-semibold px-5 pt-4 pb-2 text-cyan-300">📋 每日明細</h3>
          <table class="w-full">
            <thead><tr class="bg-ocean-800/60">
              <th class="text-left px-5 py-2 text-sm font-semibold">日期</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">消耗</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">訊息</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">對話</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">較前日</th>
            </tr></thead>
            <tbody>
              <tr v-for="d in kiroDailyData" :key="d.date" class="border-t border-white/5 hover:bg-white/5">
                <td class="px-5 py-2 text-sm">{{ d.date }}</td>
                <td class="px-5 py-2 text-sm text-right font-medium">{{ d.credits.toFixed(1) }}</td>
                <td class="px-5 py-2 text-sm text-right">{{ d.messages }}</td>
                <td class="px-5 py-2 text-sm text-right">{{ d.conversations }}</td>
                <td class="px-5 py-2 text-sm text-right">
                  <span v-if="d.change !== null" :class="d.change > 0 ? 'text-red-400' : d.change < 0 ? 'text-green-400' : 'text-white/50'">
                    {{ d.change > 0 ? '+' : '' }}{{ d.change.toFixed(0) }}%
                  </span>
                  <span v-else class="text-white/30">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Per User Detail Table -->
        <div v-if="usageData.periods.length" class="glass rounded-xl overflow-hidden">
          <h3 class="font-semibold px-5 pt-4 pb-2 text-cyan-300">👥 每人明細</h3>
          <table class="w-full">
            <thead><tr class="bg-ocean-800/60">
              <th class="text-left px-5 py-2 text-sm font-semibold">使用者</th>
              <th class="text-center px-5 py-2 text-sm font-semibold">Tier</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">額度</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">已用</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">使用率</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">訊息</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">對話</th>
            </tr></thead>
            <tbody>
              <tr v-for="u in usageData.periods[0].users" :key="u.user" class="border-t border-white/5 hover:bg-white/5">
                <td class="px-5 py-2 text-sm font-medium">{{ u.user }}</td>
                <td class="px-5 py-2 text-sm text-center">{{ u.tier }}</td>
                <td class="px-5 py-2 text-sm text-right">{{ u.limit }}</td>
                <td class="px-5 py-2 text-sm text-right font-medium">{{ u.credits.toFixed(1) }}</td>
                <td class="px-5 py-2 text-sm text-right" :class="u.pct >= 90 ? 'text-red-400' : u.pct >= 70 ? 'text-yellow-400' : ''">{{ u.pct.toFixed(1) }}%</td>
                <td class="px-5 py-2 text-sm text-right">{{ u.messages }}</td>
                <td class="px-5 py-2 text-sm text-right">{{ u.conversations }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>

    <!-- OpenAI Costs Tab -->
    <div v-if="!loading && activeTab === 'openai'" class="space-y-6">
      <div v-if="!openaiData" class="text-center py-12 text-white/50">尚無資料，請點擊「更新」查詢</div>
      <template v-else>
        <!-- Summary Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-cyan-300">${{ totalCost }}</div>
            <div class="text-xs text-white/50 mt-1">區間總費用</div>
          </div>
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-cyan-300">${{ dailyAvg }}</div>
            <div class="text-xs text-white/50 mt-1">日均費用</div>
          </div>
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-purple-300">{{ imageCount }}</div>
            <div class="text-xs text-white/50 mt-1">圖片生成數</div>
          </div>
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-purple-300">{{ imageAvgCost }}</div>
            <div class="text-xs text-white/50 mt-1">每張平均成本</div>
          </div>
        </div>

        <!-- Daily Trend Chart -->
        <div v-if="openaiData.costs && openaiData.costs.by_day && openaiData.costs.by_day.length" class="glass rounded-xl p-5">
          <h3 class="font-semibold mb-3 text-cyan-300">📈 每日費用趨勢</h3>
          <div class="h-48"><canvas ref="costChart"></canvas></div>
        </div>

        <!-- Daily Detail Table -->
        <div v-if="dailyDetails.length" class="glass rounded-xl overflow-hidden">
          <h3 class="font-semibold px-5 pt-4 pb-2 text-cyan-300">📋 每日明細</h3>
          <table class="w-full">
            <thead><tr class="bg-ocean-800/60">
              <th class="text-left px-5 py-2 text-sm font-semibold">日期</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">費用</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">較前日</th>
            </tr></thead>
            <tbody>
              <tr v-for="d in dailyDetails" :key="d.date" class="border-t border-white/5 hover:bg-white/5">
                <td class="px-5 py-2 text-sm">{{ d.date }}</td>
                <td class="px-5 py-2 text-sm text-right font-medium">${{ d.cost.toFixed(4) }}</td>
                <td class="px-5 py-2 text-sm text-right">
                  <span v-if="d.change !== null" :class="d.change > 0 ? 'text-red-400' : d.change < 0 ? 'text-green-400' : 'text-white/50'">
                    {{ d.change > 0 ? '+' : '' }}{{ d.change.toFixed(0) }}%
                  </span>
                  <span v-else class="text-white/30">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- By Model Cost -->
        <div v-if="modelDetails.length" class="glass rounded-xl overflow-hidden">
          <h3 class="font-semibold px-5 pt-4 pb-2 text-cyan-300">🤖 按模型費用</h3>
          <table class="w-full">
            <thead><tr class="bg-ocean-800/60">
              <th class="text-left px-5 py-2 text-sm font-semibold">模型</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">費用</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">佔比</th>
            </tr></thead>
            <tbody>
              <tr v-for="m in modelDetails" :key="m.model" class="border-t border-white/5 hover:bg-white/5">
                <td class="px-5 py-2 text-sm">{{ m.model }}</td>
                <td class="px-5 py-2 text-sm text-right font-medium">${{ m.cost.toFixed(4) }}</td>
                <td class="px-5 py-2 text-sm text-right text-white/60">{{ m.pct }}%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Token Usage -->
        <div v-if="tokenDetails.length" class="glass rounded-xl overflow-hidden">
          <h3 class="font-semibold px-5 pt-4 pb-2 text-cyan-300">🔤 Token 用量</h3>
          <div class="grid grid-cols-3 gap-4 px-5 py-3">
            <div class="text-center">
              <div class="text-2xl font-bold">{{ formatNum(openaiData.tokens.total_input_tokens) }}</div>
              <div class="text-xs text-white/50">Input Tokens</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold">{{ formatNum(openaiData.tokens.total_output_tokens) }}</div>
              <div class="text-xs text-white/50">Output Tokens</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold">{{ formatNum(openaiData.tokens.total_requests) }}</div>
              <div class="text-xs text-white/50">Requests</div>
            </div>
          </div>
          <table class="w-full">
            <thead><tr class="bg-ocean-800/60">
              <th class="text-left px-5 py-2 text-sm font-semibold">模型</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">Input</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">Output</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">Requests</th>
            </tr></thead>
            <tbody>
              <tr v-for="m in tokenDetails" :key="m.model" class="border-t border-white/5 hover:bg-white/5">
                <td class="px-5 py-2 text-sm">{{ m.model }}</td>
                <td class="px-5 py-2 text-sm text-right">{{ formatNum(m.input_tokens) }}</td>
                <td class="px-5 py-2 text-sm text-right">{{ formatNum(m.output_tokens) }}</td>
                <td class="px-5 py-2 text-sm text-right">{{ formatNum(m.requests) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'
import { useApi } from '../composables/useApi.js'

const { get } = useApi()

const range = ref('1')
const activeTab = ref('openai')
const loading = ref(false)
const usageData = ref(null)
const openaiData = ref(null)
const costChart = ref(null)
const kiroChart = ref(null)
const kiroStackedChart = ref(null)
const cacheTime = ref('')
let chartInstance = null
let kiroChartInstance = null
let kiroStackedInstance = null

const tabs = [
  { key: 'openai', label: '💰 OpenAI 費用' },
  { key: 'usage', label: '📊 Kiro 額度' },
]
const medals = { 0: '🥇', 1: '🥈', 2: '🥉' }

const totalCost = computed(() => openaiData.value?.costs?.total_cost?.toFixed(2) || '0.00')

const dailyAvg = computed(() => {
  const days = openaiData.value?.costs?.by_day?.length || 1
  return ((openaiData.value?.costs?.total_cost || 0) / days).toFixed(2)
})

const imageCount = computed(() => {
  if (!openaiData.value?.tokens?.by_model) return 0
  return openaiData.value.tokens.by_model
    .filter(m => (m.model || '').includes('image') || (m.model || '').includes('dall'))
    .reduce((s, m) => s + (m.requests || 0), 0)
})

const imageAvgCost = computed(() => {
  const count = imageCount.value
  if (!count || !openaiData.value?.costs?.total_cost) return '-'
  // Estimate image cost by ratio of image tokens to total tokens
  const totalOutput = openaiData.value.tokens?.total_output_tokens || 1
  const imageTokens = openaiData.value.tokens?.total_output_image_tokens || 0
  if (!imageTokens) return '-'
  const estimatedCost = openaiData.value.costs.total_cost * (imageTokens / totalOutput)
  return '$' + (estimatedCost / count).toFixed(3)
})

const dailyDetails = computed(() => {
  if (!openaiData.value?.costs?.by_day) return []
  const days = [...openaiData.value.costs.by_day].reverse()
  return days.map((d, i) => {
    const prev = days[i + 1]
    let change = null
    if (prev && prev.cost > 0) change = ((d.cost - prev.cost) / prev.cost) * 100
    return { ...d, change }
  })
})

const modelDetails = computed(() => {
  if (!openaiData.value?.costs?.by_model) return []
  const total = openaiData.value.costs.total_cost || 1
  return openaiData.value.costs.by_model.map(m => ({
    model: m.model || '（未分類）',
    cost: m.cost,
    pct: (m.cost / total * 100).toFixed(1),
  }))
})

const tokenDetails = computed(() => {
  if (!openaiData.value?.tokens?.by_model) return []
  return openaiData.value.tokens.by_model.map(m => ({
    model: m.model || '（未分類）',
    input_tokens: m.input_tokens || 0,
    output_tokens: m.output_tokens || 0,
    requests: m.requests || 0,
  }))
})

// Kiro computed
const kiroTotalUsed = computed(() => {
  if (!usageData.value?.periods?.[0]?.users) return '0'
  return usageData.value.periods[0].users.reduce((s, u) => s + u.credits, 0).toFixed(1)
})

const kiroDailyAvg = computed(() => {
  if (!usageData.value?.daily_totals?.length) {
    // Fallback: estimate from period total / days in month
    if (!usageData.value?.periods?.[0]?.users) return '0'
    const total = usageData.value.periods[0].users.reduce((s, u) => s + u.credits, 0)
    const now = new Date()
    const dayOfMonth = now.getDate()
    return (total / dayOfMonth).toFixed(1)
  }
  const days = usageData.value.daily_totals
  const credits = days.map(d => d.credits).sort((a, b) => a - b)
  // Calculate median
  const mid = Math.floor(credits.length / 2)
  const median = credits.length % 2 ? credits[mid] : (credits[mid - 1] + credits[mid]) / 2
  // Exclude days below 30% of median (holidays/low-usage days)
  const threshold = median * 0.3
  const workDays = days.filter(d => d.credits >= threshold)
  if (!workDays.length) return '0'
  const total = workDays.reduce((s, d) => s + d.credits, 0)
  return (total / workDays.length).toFixed(1)
})

const kiroTopUser = computed(() => {
  if (!usageData.value?.periods?.[0]?.users?.length) return '-'
  const sorted = [...usageData.value.periods[0].users].sort((a, b) => b.credits - a.credits)
  return sorted[0]?.user || '-'
})

const kiroRemainDays = computed(() => {
  if (!usageData.value?.periods?.[0]?.users) return '-'
  const users = usageData.value.periods[0].users
  const avgDaily = parseFloat(kiroDailyAvg.value)
  if (!avgDaily || avgDaily === 0) return '-'
  const totalRemain = users.reduce((s, u) => s + Math.max(0, u.limit - u.credits), 0)
  const days = Math.floor(totalRemain / avgDaily)
  return days > 365 ? '> 1年' : days + '天'
})

const kiroDailyData = computed(() => {
  if (!usageData.value?.daily_totals) return []
  const days = [...usageData.value.daily_totals].reverse()
  return days.map((d, i) => {
    const prev = days[i + 1]
    let change = null
    if (prev && prev.credits > 0) change = ((d.credits - prev.credits) / prev.credits) * 100
    return { ...d, change }
  })
})

async function loadAll(forceRefresh = false) {
  loading.value = true
  try {
    const refresh = forceRefresh ? '&refresh=1' : ''
    const [uRes, oRes] = await Promise.all([
      get(`/api/costs/kiro-usage?range=${range.value}${refresh}`),
      get(`/api/costs/openai?range=${range.value}&type=all`),
    ])
    usageData.value = uRes?.data || null
    openaiData.value = oRes?.data || null

    if (usageData.value?.periods) {
      const limits = { PRO: 1000, 'PRO_PLUS': 2000, 'PRO+': 2000, POWER: 10000 }
      usageData.value.periods.forEach(p => {
        p.users.forEach(u => {
          u.limit = limits[u.tier] || 1000
          u.pct = u.credits / u.limit * 100
        })
      })
    }

    const now = new Date()
    const pad = n => String(n).padStart(2, '0')
    cacheTime.value = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
  } catch (e) { console.error('Load costs failed:', e) }
  loading.value = false

  await nextTick()
  setTimeout(() => { renderCostChart(); renderKiroStackedChart(); }, 100)
}

function renderKiroChart() {
  if (!usageData.value?.daily_totals?.length || !kiroChart.value) return
  if (kiroChartInstance) kiroChartInstance.destroy()
  const days = usageData.value.daily_totals
  kiroChartInstance = new Chart(kiroChart.value, {
    type: 'line',
    data: {
      labels: days.map(d => d.date),
      datasets: [{ data: days.map(d => d.credits), borderColor: '#4fc3f7', backgroundColor: '#4fc3f722', fill: true, tension: 0.3, pointRadius: 2, borderWidth: 2 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: '#bbb', font: { size: 10 }, maxRotation: 0, maxTicksLimit: 15 }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { color: '#bbb', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } }
      },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.parsed.y.toFixed(1) + ' credits' } } }
    }
  })
}

function renderKiroStackedChart() {
  if (!usageData.value?.daily_by_user?.length || !kiroStackedChart.value) return
  if (kiroStackedInstance) kiroStackedInstance.destroy()

  const raw = usageData.value.daily_by_user
  const dates = [...new Set(raw.map(r => r.date))].sort()
  const users = [...new Set(raw.map(r => r.userid || r.user || 'unknown'))]
  const colors = ['#4fc3f7', '#ff7043', '#66bb6a', '#ab47bc', '#ffa726', '#26c6da', '#ef5350', '#8d6e63', '#78909c', '#d4e157']

  const datasets = users.map((user, i) => ({
    label: user.split('@')[0],
    data: dates.map(d => {
      const entry = raw.find(r => r.date === d && (r.userid || r.user || 'unknown') === user)
      return entry ? (entry.credits_used || entry.credits || 0) : 0
    }),
    backgroundColor: colors[i % colors.length],
    borderRadius: 2,
  }))

  kiroStackedInstance = new Chart(kiroStackedChart.value, {
    type: 'bar',
    data: { labels: dates, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { stacked: true, ticks: { color: '#bbb', font: { size: 10 }, maxRotation: 0, maxTicksLimit: 15 }, grid: { display: false } },
        y: { stacked: true, beginAtZero: true, ticks: { color: '#bbb', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } }
      },
      plugins: { legend: { display: true, position: 'bottom', labels: { color: '#bbb', font: { size: 10 }, boxWidth: 12 } }, tooltip: { mode: 'index', intersect: false, callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)} credits`, footer: items => `合計: ${items.reduce((s, i) => s + i.parsed.y, 0).toFixed(1)} credits` } } }
    }
  })
}

function renderCostChart() {
  if (!openaiData.value?.costs?.by_day?.length || !costChart.value) return
  if (chartInstance) chartInstance.destroy()
  const days = openaiData.value.costs.by_day
  chartInstance = new Chart(costChart.value, {
    type: 'bar',
    data: {
      labels: days.map(d => d.date),
      datasets: [{ data: days.map(d => d.cost), backgroundColor: '#4fc3f744', borderColor: '#4fc3f7', borderWidth: 1, borderRadius: 3 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: '#bbb', font: { size: 10 }, maxRotation: 0, maxTicksLimit: 15 }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { color: '#bbb', font: { size: 10 }, callback: v => '$' + v.toFixed(2) }, grid: { color: 'rgba(255,255,255,0.05)' } }
      },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => '$' + ctx.parsed.y.toFixed(4) } } }
    }
  })
}

watch(activeTab, async () => {
  await nextTick()
  setTimeout(() => { renderCostChart(); renderKiroStackedChart(); }, 100)
})

function barColor(pct) {
  if (pct >= 90) return 'bg-red-500'
  if (pct >= 70) return 'bg-yellow-500'
  return 'bg-cyan-500'
}

function formatNum(n) {
  if (!n) return '0'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toString()
}

function switchTab(key) {
  activeTab.value = key
  window.location.hash = key
}

onMounted(() => {
  const hash = window.location.hash.replace('#', '')
  if (hash && tabs.some(t => t.key === hash)) activeTab.value = hash
  loadAll(false)
})
</script>
