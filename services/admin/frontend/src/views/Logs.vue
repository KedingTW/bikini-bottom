<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">Log 搜尋</span>
  </div>

  <div class="p-7 space-y-4">
    <div v-if="!agentList.length" class="text-center py-20 text-white/50">
      <div class="text-4xl mb-3">📋</div>
      <div>此伺服器尚未配置角色</div>
    </div>
    <template v-else>
    <!-- Filters -->
    <div class="glass rounded-xl p-4 flex items-center gap-3 flex-wrap">
      <input v-model="keyword" placeholder="關鍵字..." @keyup.enter="search()"
        class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm w-52 focus:outline-none focus:border-cyan-400/60">
      <select v-model="sinceHours" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm">
        <option :value="1">最近 1 小時</option>
        <option :value="6">最近 6 小時</option>
        <option :value="24">最近 24 小時</option>
        <option :value="72">最近 3 天</option>
        <option :value="168">最近 7 天</option>
      </select>
      <div class="flex items-center gap-2">
        <label v-for="a in agentList" :key="a.id" class="flex items-center gap-1 text-xs">
          <input type="checkbox" :value="a.id" v-model="selectedAgents" class="w-3 h-3 rounded">
          <span class="text-white/70">{{ a.name }}</span>
        </label>
      </div>
      <button @click="selectAll()" class="text-xs text-cyan-400 hover:text-cyan-300">全選</button>
      <button @click="selectedAgents = []" class="text-xs text-white/40 hover:text-white/60">清除</button>
      <button @click="search()" :disabled="searching" class="ml-auto bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white rounded px-3 py-1.5 text-sm font-medium">{{ searching ? '搜尋中...' : '🔍 搜尋' }}</button>
    </div>

    <!-- Tail Mode -->
    <div class="glass rounded-xl p-4">
      <div class="flex items-center gap-3 mb-3">
        <h3 class="font-semibold text-cyan-300 text-sm">📡 即時 Log（tail -f）</h3>
        <select v-model="tailAgent" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-xs">
          <option value="">選擇角色...</option>
          <option v-for="a in agentList" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
        <button v-if="!tailing" @click="startTail()" :disabled="!tailAgent" class="text-xs px-3 py-1 rounded bg-green-600 hover:bg-green-500 disabled:opacity-40 text-white">▶ 開始</button>
        <button v-else @click="stopTail()" class="text-xs px-3 py-1 rounded bg-red-600 hover:bg-red-500 text-white">⏹ 停止</button>
        <span v-if="tailing" class="text-xs text-green-400 animate-pulse">● 監聽中</span>
      </div>
      <div v-if="tailLines.length" ref="tailScroll" class="bg-ocean-800/50 rounded-lg p-3 max-h-60 overflow-y-auto font-mono text-xs text-white/80 leading-relaxed">
        <div v-for="(line, i) in tailLines" :key="i">{{ line }}</div>
      </div>
    </div>

    <!-- Search Results -->
    <div v-if="results.length" class="space-y-3">
      <div class="flex items-center gap-3">
        <h3 class="font-semibold text-cyan-300">搜尋結果</h3>
        <span class="text-xs text-white/40">{{ totalLines }} 行符合</span>
        <a :href="exportUrl" target="_blank" class="ml-auto text-xs px-3 py-1 rounded border border-white/20 text-white/70 hover:bg-white/10">📥 匯出全部 Log</a>
      </div>
      <div v-for="r in results" :key="r.agent" class="glass rounded-xl overflow-hidden">
        <div class="px-4 py-2 bg-ocean-800/60 flex items-center gap-2">
          <span class="font-medium text-sm text-cyan-300">{{ r.agent }}</span>
          <span class="text-xs text-white/40">{{ r.total }} 行符合</span>
        </div>
        <div class="p-3 max-h-64 overflow-y-auto font-mono text-xs text-white/70 leading-relaxed">
          <div v-for="(line, i) in r.lines" :key="i" v-html="highlight(line)"></div>
        </div>
      </div>
    </div>
    <div v-else-if="searched && !searching" class="text-center py-8 text-white/50">沒有找到符合的 log</div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, inject } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const agentList = ref([])
const keyword = ref('')
const sinceHours = ref(24)
const selectedAgents = ref([])
const searching = ref(false)
const searched = ref(false)
const results = ref([])

async function loadAgents() {
  const res = await get(`/api/agents?group=${currentGroup.value}`)
  const agents = res?.agents || []
  agentList.value = agents.map(a => ({ id: a.deployment || a.name, name: a.display }))
  agentList.value.push({ id: 'admin', name: '管理後台' })
  selectedAgents.value = agentList.value.map(a => a.id)
}

// Tail mode
const tailAgent = ref('')
const tailing = ref(false)
const tailLines = ref([])
const tailScroll = ref(null)
let tailInterval = null

const totalLines = computed(() => results.value.reduce((s, r) => s + r.total, 0))
const exportUrl = computed(() => `/api/logs/export?agents=${selectedAgents.value.join(',')}&since_hours=${sinceHours.value}`)

function selectAll() { selectedAgents.value = agentList.value.map(a => a.id) }

async function search() {
  searching.value = true
  searched.value = true
  results.value = []
  const res = await get(`/api/logs/search?keyword=${encodeURIComponent(keyword.value)}&agents=${selectedAgents.value.join(',')}&since_hours=${sinceHours.value}`)
  if (res) results.value = res.results || []
  searching.value = false
}

function highlight(line) {
  if (!keyword.value) return escHtml(line)
  const escaped = keyword.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return escHtml(line).replace(new RegExp(`(${escaped})`, 'gi'), '<span class="bg-yellow-500/40 text-yellow-200 px-0.5 rounded">$1</span>')
}

function escHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

async function startTail() {
  if (!tailAgent.value) return
  tailing.value = true
  tailLines.value = []
  await fetchTail()
  tailInterval = setInterval(fetchTail, 3000)
}

function stopTail() {
  tailing.value = false
  if (tailInterval) { clearInterval(tailInterval); tailInterval = null }
}

async function fetchTail() {
  const res = await get(`/api/logs/${tailAgent.value}?lines=50`)
  if (res?.logs) {
    tailLines.value = res.logs.split('\n').slice(-100)
    await nextTick()
    if (tailScroll.value) tailScroll.value.scrollTop = tailScroll.value.scrollHeight
  }
}

onMounted(() => {
  loadAgents()
  window.addEventListener('group-changed', loadAgents)
})
onUnmounted(() => { if (tailInterval) clearInterval(tailInterval) })
</script>
