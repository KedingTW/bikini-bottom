<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">討論串管理</span>
    <button @click="refresh()" class="ml-auto bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </div>

  <div class="p-7">
    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-4"></div>
      <span class="text-white/60 text-sm">載入中...</span>
    </div>

    <!-- Members Tab -->
    <div v-if="!loading && activeTab === 'members'">
      <div class="mb-4 flex items-center gap-3">
        <input v-model="memberSearch" placeholder="搜尋成員..." class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm w-64 focus:outline-none focus:border-cyan-400/60">
        <span class="text-white/50 text-xs">共 {{ filteredMembers.length }} 人</span>
      </div>
      <div class="glass rounded-xl overflow-hidden">
        <table class="w-full">
          <thead><tr class="bg-ocean-800/60">
            <th class="text-left px-5 py-2 text-sm font-semibold">成員</th>
            <th class="text-left px-5 py-2 text-sm font-semibold">暱稱</th>
            <th class="text-left px-5 py-2 text-sm font-semibold">身分組</th>
            <th class="text-left px-5 py-2 text-sm font-semibold">加入時間</th>
          </tr></thead>
          <tbody>
            <tr v-for="m in filteredMembers" :key="m.id" class="border-t border-white/5 hover:bg-white/5">
              <td class="px-5 py-2 text-sm">
                <div class="flex items-center gap-2">
                  <img v-if="m.avatar" :src="`https://cdn.discordapp.com/avatars/${m.id}/${m.avatar}.png?size=32`" class="w-7 h-7 rounded-full">
                  <div v-else class="w-7 h-7 rounded-full bg-cyan-700 flex items-center justify-center text-xs font-bold text-white">{{ m.display_name.charAt(0) }}</div>
                  <span>{{ m.display_name }}</span>
                  <span v-if="m.username !== m.display_name" class="text-white/40 text-xs">@{{ m.username }}</span>
                </div>
              </td>
              <td class="px-5 py-2 text-sm text-white/70">{{ m.nick || '-' }}</td>
              <td class="px-5 py-2 text-sm">
                <div class="flex flex-wrap gap-1">
                  <span v-for="rid in m.roles" :key="rid" class="text-xs px-1.5 py-0.5 rounded bg-white/10" :style="{color: getRoleColor(rid)}">{{ getRoleName(rid) }}</span>
                </div>
              </td>
              <td class="px-5 py-2 text-sm text-white/50">{{ formatDate(m.joined_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Roles Tab -->
    <div v-if="!loading && activeTab === 'roles'">
      <div class="space-y-4">
        <div v-for="r in roles" :key="r.id" class="glass rounded-xl p-4">
          <div class="flex items-center gap-3 mb-2">
            <div v-if="r.color" class="w-3 h-3 rounded-full" :style="{background: '#' + r.color.toString(16).padStart(6, '0')}"></div>
            <span class="font-medium" :style="{color: r.color ? '#' + r.color.toString(16).padStart(6, '0') : 'inherit'}">{{ r.name }}</span>
            <span class="text-white/40 text-xs ml-auto">{{ getRoleMembers(r.id).length }} 人</span>
          </div>
          <div v-if="getRoleMembers(r.id).length" class="flex flex-wrap gap-2">
            <div v-for="m in getRoleMembers(r.id)" :key="m.id" class="flex items-center gap-1.5 bg-ocean-800/60 rounded-full px-2.5 py-1 text-xs">
              <img v-if="m.avatar" :src="`https://cdn.discordapp.com/avatars/${m.id}/${m.avatar}.png?size=16`" class="w-4 h-4 rounded-full">
              <div v-else class="w-4 h-4 rounded-full bg-cyan-700 flex items-center justify-center text-[10px] font-bold">{{ m.display_name.charAt(0) }}</div>
              <span>{{ m.display_name }}</span>
            </div>
          </div>
          <div v-else class="text-white/30 text-xs">無成員</div>
        </div>
      </div>
    </div>

    <!-- Threads -->
    <div v-if="!loading">
      <div v-if="!threads.length" class="text-center py-12 text-white/50">沒有活躍的討論串</div>
      <div v-else>
        <!-- Toolbar -->
        <div class="flex items-center gap-3 mb-4 flex-wrap">
          <input v-model="threadFilter" placeholder="搜尋討論串..." class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm w-52 focus:outline-none focus:border-cyan-400/60">
          <select v-model="threadTagFilter" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm">
            <option value="">全部標籤</option>
            <option v-for="tag in allTags" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
          </select>
          <select v-model="threadChannelFilter" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm">
            <option value="">全部頻道</option>
            <option v-for="ch in forumChannels" :key="ch.id" :value="ch.id">#{{ ch.name }}</option>
          </select>
          <select v-model="threadSort" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm">
            <option value="idle">最久未動</option>
            <option value="active">最近活動</option>
            <option value="messages">訊息最多</option>
          </select>
          <span class="text-white/40 text-xs">{{ sortedFilteredThreads.length }} / {{ threads.length }} 個</span>
          <!-- Batch actions -->
          <div v-if="selectedThreads.length" class="ml-auto flex items-center gap-2">
            <span class="text-xs text-white/50">已選 {{ selectedThreads.length }} 個</span>
            <button @click="batchClose()" class="text-xs px-3 py-1.5 rounded bg-green-600 hover:bg-green-500 text-white font-medium">🏷️ 批次結案</button>
            <button @click="batchArchive()" class="text-xs px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-white font-medium">📦 批次封存</button>
          </div>
        </div>

        <!-- Thread List -->
        <div class="space-y-1.5">
          <div v-for="t in sortedFilteredThreads" :key="t.id"
            class="glass rounded-lg px-4 py-3 flex items-center gap-3"
            :class="getIdleDays(t) >= 7 ? 'border-l-4 border-yellow-500' : getIdleDays(t) >= 14 ? 'border-l-4 border-red-500' : ''">
            <!-- Checkbox -->
            <input type="checkbox" :value="t.id" v-model="selectedThreads" class="w-4 h-4 rounded bg-ocean-800 border-white/30">
            <!-- Content (clickable for preview) -->
            <div class="flex-1 min-w-0 cursor-pointer" @click="openPreview(t)">
              <div class="flex items-center gap-2">
                <span class="font-medium truncate text-sm">{{ t.name }}</span>
                <span v-if="getIdleDays(t) >= 7" class="text-xs px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-300">閒置 {{ getIdleDays(t) }}天</span>
              </div>
              <div class="flex items-center gap-2 mt-1 flex-wrap">
                <span class="text-xs text-white/40">#{{ getChannelName(t.parent_id) }}</span>
                <span class="text-xs text-white/40">💬 {{ t.message_count }}</span>
                <span class="text-xs text-white/40">{{ t.last_activity ? t.last_activity.slice(5) : '' }}</span>
                <span v-for="tagId in t.applied_tags" :key="tagId"
                  class="text-xs px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">{{ getTagName(t.parent_id, tagId) }}</span>
              </div>
            </div>
            <!-- Actions -->
            <button @click="closeThread(t)" class="text-xs px-2 py-1 rounded border border-green-400/30 text-green-300 hover:bg-green-400/10" title="結案">🏷️</button>
            <button @click="archiveThread(t.id)" class="text-xs px-2 py-1 rounded border border-white/20 text-white/70 hover:bg-white/10" title="封存">📦</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Activity Tab -->
    <div v-if="!loading && activeTab === 'activity'">
      <div v-if="activityLoading" class="flex flex-col items-center justify-center py-20">
        <div class="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-4"></div>
        <span class="text-white/60 text-sm">統計中...</span>
      </div>
      <div v-else-if="!activityData" class="text-center py-12 text-white/50">載入中...</div>
      <template v-else>
        <!-- Summary -->
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-cyan-300">{{ activityData.total_threads }}</div>
            <div class="text-xs text-white/50 mt-1">活躍討論串（未封存）</div>
          </div>
          <div class="glass rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-cyan-300">{{ totalMessages }}</div>
            <div class="text-xs text-white/50 mt-1">總訊息數</div>
          </div>
        </div>

        <!-- Daily Post Chart -->
        <div class="glass rounded-xl p-5 mb-6" v-show="activityData.daily_chart && activityData.daily_chart.length">
          <h3 class="font-semibold mb-3 text-cyan-300">📈 每日新增討論串</h3>
          <div class="h-48"><canvas :ref="el => { activityChart = el; if(el) renderActivityChart() }"></canvas></div>
        </div>

        <!-- Top Threads -->
        <div v-if="activityData.top_threads && activityData.top_threads.length" class="glass rounded-xl overflow-hidden">
          <h3 class="font-semibold px-5 pt-4 pb-2 text-cyan-300">🔥 熱門討論串（點擊查看對話分析）</h3>
          <table class="w-full">
            <thead><tr class="bg-ocean-800/60">
              <th class="text-left px-5 py-2 text-sm font-semibold">討論串</th>
              <th class="text-left px-5 py-2 text-sm font-semibold">建立者</th>
              <th class="text-left px-5 py-2 text-sm font-semibold">頻道</th>
              <th class="text-left px-5 py-2 text-sm font-semibold">標籤</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">訊息</th>
              <th class="text-right px-5 py-2 text-sm font-semibold">最後對話</th>
            </tr></thead>
            <tbody>
              <tr v-for="t in activityData.top_threads" :key="t.id" class="border-t border-white/5 hover:bg-white/5 cursor-pointer" @click="openThreadDetail(t)">
                <td class="px-5 py-2 text-sm font-medium truncate max-w-[250px]">{{ t.name }}</td>
                <td class="px-5 py-2 text-sm">
                  <div class="flex items-center gap-1.5">
                    <div class="w-5 h-5 rounded-full bg-cyan-700 flex items-center justify-center text-[10px] font-bold">{{ getOwnerName(t.owner_id).charAt(0) }}</div>
                    <span class="text-white/70">{{ getOwnerName(t.owner_id) }}</span>
                  </div>
                </td>
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

        <!-- Thread Detail Dialog -->
        <div v-if="threadDetail" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="threadDetail = null">
          <div class="bg-ocean-700 rounded-xl w-[92%] max-w-[900px] flex flex-col shadow-2xl max-h-[85vh]">
            <div class="px-6 py-4 border-b border-white/10 flex items-center gap-3 font-semibold shrink-0">
              <span>📊 {{ threadDetail.name }}</span>
              <span class="text-sm font-normal text-white/50">{{ threadDetail.message_count }} 則訊息</span>
              <button @click="threadDetail = null" class="ml-auto text-2xl text-white/60 hover:text-white">&times;</button>
            </div>
            <div class="px-6 py-5 overflow-y-auto">
              <div v-if="threadDetailLoading" class="flex items-center justify-center py-12">
                <div class="w-8 h-8 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
              </div>
              <div v-show="!threadDetailLoading">
                <div class="h-[250px] mb-4"><canvas ref="threadChart"></canvas></div>
                <p class="text-xs text-white/40 text-center mb-6">對話密度（每小時訊息數）</p>
                <!-- Author Stats -->
                <div class="flex gap-4 mt-4">
                  <!-- Automation Index -->
                  <div v-if="automationIndex" class="glass rounded-lg p-4 w-48 text-center shrink-0">
                    <div class="text-3xl font-bold" :class="automationIndex.score >= 70 ? 'text-green-400' : automationIndex.score >= 40 ? 'text-yellow-400' : 'text-red-400'">{{ automationIndex.score }}%</div>
                    <div class="text-xs text-white/50 mt-1">自動化指數</div>
                    <div class="text-xs text-white/40 mt-2">🤖 {{ automationIndex.botMsgs }} / 👤 {{ automationIndex.humanMsgs }}</div>
                  </div>
                  <!-- Participants -->
                  <div v-if="threadAuthorStats.length" class="flex-1">
                    <h4 class="text-sm font-semibold text-cyan-300 mb-3">👥 參與者</h4>
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                      <div v-for="a in threadAuthorStats" :key="a.name" class="flex items-center gap-2 bg-ocean-800/50 rounded px-3 py-2">
                        <div class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" :class="a.is_bot ? 'bg-purple-700' : 'bg-cyan-700'">{{ a.is_bot ? '🤖' : a.name.charAt(0) }}</div>
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
      </template>
    </div>

    <!-- Send Message Tab -->
    <div v-if="!loading && activeTab === 'message'">
      <div class="glass rounded-xl p-6 max-w-2xl">
        <h3 class="font-semibold mb-4 text-cyan-300">📢 發送公告</h3>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1">目標頻道</label>
          <select v-model="msgChannel" class="w-full bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-400/60">
            <option value="">選擇頻道...</option>
            <option v-for="c in channels" :key="c.id" :value="c.id">#{{ c.name }}</option>
          </select>
        </div>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1">訊息內容</label>
          <textarea v-model="msgContent" rows="5" class="w-full bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-400/60 resize-y" placeholder="輸入要發送的訊息..."></textarea>
        </div>
        <div class="flex items-center gap-3">
          <button @click="sendMsg" :disabled="!msgChannel || !msgContent.trim()" class="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-5 py-2 rounded text-sm font-medium transition">發送</button>
          <span v-if="msgStatus" class="text-sm" :class="msgStatus.ok ? 'text-green-400' : 'text-red-400'">{{ msgStatus.text }}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Preview Dialog -->
  <div v-if="previewThread" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="previewThread = null">
    <div class="bg-ocean-700 rounded-xl w-[90%] max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
      <div class="px-6 py-4 border-b border-white/10 flex items-center gap-3 font-semibold shrink-0">
        <span class="truncate">💬 {{ previewThread.name }}</span>
        <span class="text-sm font-normal text-white/50">{{ previewThread.message_count }} 則</span>
        <button @click="previewThread = null" class="ml-auto text-2xl text-white/60 hover:text-white">&times;</button>
      </div>
      <div class="flex-1 overflow-y-auto px-6 py-4 space-y-3" ref="previewScroll">
        <button v-if="previewHasMore" @click="loadMorePreview()" class="w-full text-center text-xs text-cyan-400 hover:text-cyan-300 py-2">⬆️ 載入更多</button>
        <div v-for="m in previewMessages" :key="m.id" class="flex gap-3">
          <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0" :class="m.is_bot ? 'bg-purple-700' : 'bg-cyan-700'">{{ m.is_bot ? '🤖' : m.author.charAt(0) }}</div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium" :class="m.is_bot ? 'text-purple-300' : ''">{{ m.author }}</span>
              <span class="text-xs text-white/40">{{ formatMsgTime(m.timestamp) }}</span>
            </div>
            <div class="text-sm text-white/80 whitespace-pre-wrap break-words mt-0.5">{{ m.content || '（無文字內容）' }}</div>
            <div v-if="m.attachments" class="text-xs text-white/40 mt-0.5">📎 {{ m.attachments }} 個附件</div>
          </div>
        </div>
        <div v-if="previewLoading" class="text-center py-4"><div class="w-6 h-6 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin inline-block"></div></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import Chart from 'chart.js/auto'
import { useApi } from '../composables/useApi.js'

const { get, post, put } = useApi()

const activeTab = ref('threads')
const loading = ref(false)
const members = ref([])
const roles = ref([])
const channels = ref([])
const memberSearch = ref('')
const msgChannel = ref('')
const msgContent = ref('')
const msgStatus = ref(null)
const threads = ref([])
const tagsMap = ref({})
const threadFilter = ref('')
const threadTagFilter = ref('')
const threadChannelFilter = ref('')
const threadSort = ref('idle')
const selectedThreads = ref([])
const previewThread = ref(null)
const previewMessages = ref([])
const previewLoading = ref(false)
const previewHasMore = ref(false)
const previewScroll = ref(null)
const activityData = ref(null)
const activityLoading = ref(false)
const activityChart = ref(null)
const threadDetail = ref(null)
const threadDetailLoading = ref(false)
const threadChart = ref(null)
const threadMessages = ref([])
let activityChartInstance = null
let threadChartInstance = null

const tabs = [
  { key: 'threads', label: '📌 討論串' },
]

const filteredMembers = computed(() => {
  if (!memberSearch.value) return members.value
  const q = memberSearch.value.toLowerCase()
  return members.value.filter(m =>
    m.display_name.toLowerCase().includes(q) ||
    m.username.toLowerCase().includes(q) ||
    (m.nick || '').toLowerCase().includes(q)
  )
})

function getRoleName(id) {
  const r = roles.value.find(r => r.id === id)
  return r ? r.name : id
}

function getRoleMembers(roleId) {
  return members.value.filter(m => m.roles.includes(roleId))
}

function getRoleColor(id) {
  const r = roles.value.find(r => r.id === id)
  if (r && r.color) return '#' + r.color.toString(16).padStart(6, '0')
  return '#aaa'
}

function formatDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}/${String(d.getMonth()+1).padStart(2,'0')}/${String(d.getDate()).padStart(2,'0')}`
}

function switchTab(key) {
  activeTab.value = key
  window.location.hash = key
  if (key === 'threads' && !threads.value.length) loadThreads()
  if (key === 'activity' && !activityData.value) loadActivity()
}

async function refresh() {
  loading.value = true
  try {
    const [mRes, rRes, cRes] = await Promise.all([
      get('/api/discord/members'),
      get('/api/discord/roles'),
      get('/api/discord/channels'),
    ])
    members.value = mRes?.members || []
    roles.value = rRes?.roles || []
    channels.value = cRes?.channels || []
  } catch (e) { console.error(e) }
  loading.value = false
}

async function loadThreads() {
  try {
    const res = await get('/api/discord/threads')
    threads.value = res?.threads || []
    tagsMap.value = res?.tags_map || {}
  } catch (e) { console.error(e) }
}

async function loadActivity() {
  activityLoading.value = true
  try {
    const res = await get('/api/discord/activity')
    activityData.value = res
  } catch (e) { console.error(e) }
  activityLoading.value = false
}

function renderActivityChart() {
  if (!activityData.value?.daily_chart?.length) return
  if (!activityChart.value) { console.warn('activityChart canvas not ready'); return }
  if (activityChartInstance) activityChartInstance.destroy()
  const days = activityData.value.daily_chart

  // Fill missing dates with 0
  const filled = []
  if (days.length >= 2) {
    const start = new Date(days[0].date)
    const end = new Date(days[days.length - 1].date)
    const dayMap = Object.fromEntries(days.map(d => [d.date, d.count]))
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const key = d.toISOString().slice(0, 10)
      filled.push({ date: key, count: dayMap[key] || 0 })
    }
  } else {
    filled.push(...days)
  }

  activityChartInstance = new Chart(activityChart.value, {
    type: 'line',
    data: {
      labels: filled.map(d => d.date.slice(5)),
      datasets: [{ data: filled.map(d => d.count), borderColor: '#4fc3f7', backgroundColor: '#4fc3f722', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      scales: {
        x: { ticks: { color: '#bbb', font: { size: 10 }, maxRotation: 0, maxTicksLimit: 15 }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { color: '#bbb', font: { size: 10 }, stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } }
      },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.parsed.y + ' 則貼文' } } }
    }
  })
}

async function archiveThread(threadId) {
  if (!confirm('確定要封存此討論串？')) return
  await post(`/api/discord/threads/${threadId}/archive`)
  loadThreads()
}

const filteredThreads = computed(() => {
  if (!threadFilter.value) return threads.value
  const q = threadFilter.value.toLowerCase()
  return threads.value.filter(t => t.name.toLowerCase().includes(q))
})

const allTags = computed(() => {
  const tags = []
  const seen = new Set()
  for (const [, tagList] of Object.entries(tagsMap.value)) {
    for (const t of tagList) {
      if (!seen.has(t.id)) { seen.add(t.id); tags.push(t) }
    }
  }
  return tags
})

const forumChannels = computed(() => {
  return channels.value.filter(c => c.type === 15)
})

const sortedFilteredThreads = computed(() => {
  let list = [...threads.value]
  // Text filter
  if (threadFilter.value) {
    const q = threadFilter.value.toLowerCase()
    list = list.filter(t => t.name.toLowerCase().includes(q))
  }
  // Tag filter
  if (threadTagFilter.value) {
    list = list.filter(t => t.applied_tags.includes(threadTagFilter.value))
  }
  // Channel filter
  if (threadChannelFilter.value) {
    list = list.filter(t => t.parent_id === threadChannelFilter.value)
  }
  // Sort
  if (threadSort.value === 'idle') {
    list.sort((a, b) => (a.last_activity || '').localeCompare(b.last_activity || ''))
  } else if (threadSort.value === 'active') {
    list.sort((a, b) => (b.last_activity || '').localeCompare(a.last_activity || ''))
  } else if (threadSort.value === 'messages') {
    list.sort((a, b) => b.message_count - a.message_count)
  }
  return list
})

function getIdleDays(t) {
  if (!t.last_activity) return 999
  const last = new Date(t.last_activity)
  const now = new Date()
  return Math.floor((now - last) / (1000 * 60 * 60 * 24))
}

async function closeThread(t) {
  if (!confirm(`結案「${t.name}」？將貼上「已完成」標籤並移除進行中標籤`)) return
  try {
    // Find the right tags for this thread's parent channel
    const parentTags = tagsMap.value[t.parent_id] || []
    const doneTag = parentTags.find(tag => tag.name === '已完成' || tag.name === '已結案')
    const removeTags = ['處理中', '測試中', '討論中']
    const newTags = t.applied_tags.filter(id => {
      const tag = parentTags.find(pt => pt.id === id)
      return tag && !removeTags.includes(tag.name)
    })
    if (doneTag && !newTags.includes(doneTag.id)) newTags.push(doneTag.id)
    await put(`/api/discord/threads/${t.id}/tags`, { tag_ids: newTags })
    loadThreads()
  } catch (e) { console.error(e) }
}

async function batchClose() {
  if (!confirm(`批次結案 ${selectedThreads.value.length} 個討論串？`)) return
  for (const tid of selectedThreads.value) {
    const t = threads.value.find(x => x.id === tid)
    if (t) {
      const parentTags = tagsMap.value[t.parent_id] || []
      const doneTag = parentTags.find(tag => tag.name === '已完成' || tag.name === '已結案')
      const removeTags = ['處理中', '測試中', '討論中']
      const newTags = t.applied_tags.filter(id => {
        const tag = parentTags.find(pt => pt.id === id)
        return tag && !removeTags.includes(tag.name)
      })
      if (doneTag && !newTags.includes(doneTag.id)) newTags.push(doneTag.id)
      try { await put(`/api/discord/threads/${t.id}/tags`, { tag_ids: newTags }) } catch {}
    }
  }
  selectedThreads.value = []
  loadThreads()
}

async function batchArchive() {
  if (!confirm(`批次封存 ${selectedThreads.value.length} 個討論串？（將同時結案）`)) return
  for (const tid of selectedThreads.value) {
    const t = threads.value.find(x => x.id === tid)
    if (t) {
      // Close first
      const parentTags = tagsMap.value[t.parent_id] || []
      const doneTag = parentTags.find(tag => tag.name === '已完成' || tag.name === '已結案')
      const removeTags = ['處理中', '測試中', '討論中']
      const newTags = t.applied_tags.filter(id => {
        const tag = parentTags.find(pt => pt.id === id)
        return tag && !removeTags.includes(tag.name)
      })
      if (doneTag && !newTags.includes(doneTag.id)) newTags.push(doneTag.id)
      try { await put(`/api/discord/threads/${t.id}/tags`, { tag_ids: newTags }) } catch {}
    }
    // Archive
    try { await post(`/api/discord/threads/${tid}/archive`) } catch {}
  }
  selectedThreads.value = []
  loadThreads()
}

function getChannelName(id) {
  const c = channels.value.find(c => c.id === id)
  return c ? c.name : id
}

async function openPreview(t) {
  previewThread.value = t
  previewMessages.value = []
  previewLoading.value = true
  previewHasMore.value = false
  try {
    const res = await get(`/api/discord/threads/${t.id}/messages?limit=10`)
    previewMessages.value = (res?.messages || []).reverse()
    previewHasMore.value = res?.has_more || false
  } catch (e) { console.error(e) }
  previewLoading.value = false
}

async function loadMorePreview() {
  if (!previewMessages.value.length || !previewThread.value) return
  const oldest = previewMessages.value[0]
  previewLoading.value = true
  try {
    const res = await get(`/api/discord/threads/${previewThread.value.id}/messages?limit=10&before=${oldest.id}`)
    const older = (res?.messages || []).reverse()
    previewMessages.value = [...older, ...previewMessages.value]
    previewHasMore.value = res?.has_more || false
  } catch (e) { console.error(e) }
  previewLoading.value = false
}

function formatMsgTime(ts) {
  const d = new Date(ts)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getMonth()+1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function getOwnerName(ownerId) {
  if (!ownerId) return '?'
  const m = members.value.find(m => m.id === ownerId)
  return m ? m.display_name : ownerId.slice(-4)
}

function getTagName(parentId, tagId) {
  const tags = tagsMap.value[parentId] || []
  const tag = tags.find(t => t.id === tagId)
  return tag ? tag.name : tagId
}

const totalMessages = computed(() => {
  if (!activityData.value?.top_threads) return 0
  return activityData.value.top_threads.reduce((s, t) => s + t.message_count, 0)
})

const threadAuthorStats = computed(() => {
  if (!threadMessages.value.length) return []
  const counts = {}
  threadMessages.value.forEach(m => {
    const name = m.author || 'unknown'
    counts[name] = (counts[name] || { count: 0, is_bot: m.is_bot })
    counts[name].count++
  })
  return Object.entries(counts)
    .map(([name, data]) => ({ name, count: data.count, is_bot: data.is_bot }))
    .sort((a, b) => b.count - a.count)
})

const automationIndex = computed(() => {
  if (!threadMessages.value.length) return null
  const botMsgs = threadMessages.value.filter(m => m.is_bot).length
  const total = threadMessages.value.length
  return { score: Math.round(botMsgs / total * 100), botMsgs, humanMsgs: total - botMsgs, total }
})

async function openThreadDetail(thread) {
  threadDetail.value = thread
  threadDetailLoading.value = true
  threadMessages.value = []
  await nextTick()
  try {
    const res = await get(`/api/discord/threads/${thread.id}/messages`)
    threadMessages.value = res?.messages || []
  } catch (e) { console.error(e) }
  threadDetailLoading.value = false
  await nextTick()
  setTimeout(() => renderThreadChart(null), 300)
}

function renderThreadChart(unused) {
  const messages = threadMessages.value
  if (!threadChart.value || !messages.length) return
  if (threadChartInstance) threadChartInstance.destroy()

  // Group by hour
  const timestamps = messages.map(m => new Date(m.timestamp).getTime()).sort((a, b) => a - b)
  const hourMs = 60 * 60 * 1000
  const startHour = Math.floor(timestamps[0] / hourMs) * hourMs
  const endHour = Math.floor(timestamps[timestamps.length - 1] / hourMs) * hourMs

  // Fill all hours from start to end
  const buckets = {}
  for (let t = startHour; t <= endHour; t += hourMs) {
    buckets[t] = 0
  }
  timestamps.forEach(ts => {
    const key = Math.floor(ts / hourMs) * hourMs
    buckets[key] = (buckets[key] || 0) + 1
  })

  const sorted = Object.entries(buckets).sort((a, b) => a[0] - b[0])
  const labels = sorted.map(([k]) => {
    const d = new Date(parseInt(k))
    return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:00`
  })
  const data = sorted.map(([, v]) => v)

  threadChartInstance = new Chart(threadChart.value, {
    type: 'line',
    data: {
      labels,
      datasets: [{ data, borderColor: '#4fc3f7', backgroundColor: '#4fc3f722', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 1.5 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      interaction: { intersect: false, mode: 'index' },
      scales: {
        x: { ticks: { color: '#bbb', font: { size: 9 }, maxRotation: 0, maxTicksLimit: 12 }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { color: '#bbb', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } }
      },
      plugins: { legend: { display: false }, tooltip: { enabled: true, callbacks: { label: ctx => ctx.parsed.y + ' 則訊息' } } }
    }
  })
}

watch(threadMessages, async (msgs) => {
  if (msgs.length) {
    await nextTick()
    setTimeout(() => renderThreadChart(null), 200)
  }
})

async function sendMsg() {
  if (!msgChannel.value || !msgContent.value.trim()) return
  msgStatus.value = null
  try {
    const res = await fetch(`/api/discord/channels/${msgChannel.value}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: msgContent.value })
    })
    const data = await res.json()
    if (res.ok) {
      msgStatus.value = { ok: true, text: '✅ 已發送' }
      msgContent.value = ''
    } else {
      msgStatus.value = { ok: false, text: '❌ ' + (data.detail || '發送失敗') }
    }
  } catch (e) {
    msgStatus.value = { ok: false, text: '❌ 網路錯誤' }
  }
}

onMounted(() => {
  const hash = window.location.hash.replace('#', '')
  if (hash && tabs.some(t => t.key === hash)) activeTab.value = hash
  refresh()
  if (activeTab.value === 'threads') loadThreads()
  if (activeTab.value === 'activity') loadActivity()
})
</script>
