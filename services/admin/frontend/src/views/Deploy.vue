<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm sticky top-0 z-10">
    <span class="font-medium">部署管理</span>
    <button @click="loadAll()" class="ml-auto bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </div>

  <div class="p-7 space-y-6">
    <!-- Git Status -->
    <div class="glass rounded-xl p-5">
      <h3 class="font-semibold text-cyan-300 mb-3">📦 Git 狀態</h3>
      <div v-if="git.branch" class="space-y-2 text-sm">
        <div><span class="text-white/50">Branch:</span> <span class="font-mono text-cyan-300 ml-2">{{ git.branch }}</span></div>
        <div v-if="git.uncommitted.length && git.uncommitted[0]">
          <span class="text-white/50">未提交變更:</span>
          <span class="text-yellow-300 ml-2">{{ git.uncommitted.length }} 個檔案</span>
        </div>
        <div v-if="git.log.length">
          <span class="text-white/50">最近 Commit:</span>
          <div class="mt-1 space-y-0.5 font-mono text-xs text-white/70 max-h-40 overflow-y-auto">
            <div v-for="(line, i) in git.log" :key="i">{{ line }}</div>
          </div>
        </div>
      </div>
      <div v-else class="text-white/50 text-sm">載入中...</div>
    </div>

    <!-- Deploy Actions -->
    <div class="glass rounded-xl p-5">
      <h3 class="font-semibold text-cyan-300 mb-3">🚀 一鍵部署</h3>
      <div class="flex items-center gap-3 mb-4">
        <select v-model="deployTarget" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm">
          <option value="">選擇部署目標...</option>
          <option value="admin">管理後台（admin）</option>
          <option v-for="a in agents" :key="a.id" :value="a.id">{{ a.name }}（{{ a.id }}）</option>
        </select>
        <button @click="doDeploy()" :disabled="!deployTarget || deploying"
          class="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white px-5 py-2 rounded text-sm font-medium transition">
          {{ deploying ? '部署中...' : '🚀 Build & Deploy' }}
        </button>
      </div>
      <div class="text-xs text-white/40 mb-3">流程：git pull → docker build → k3s import → restart pod</div>

      <!-- Deploy Progress -->
      <div v-if="deploySteps.length" class="space-y-1.5">
        <div v-for="(s, i) in deploySteps" :key="i" class="flex items-center gap-2 text-sm">
          <span :class="s.ok ? 'text-green-400' : 'text-red-400'">{{ s.ok ? '✅' : '❌' }}</span>
          <span class="font-medium w-28">{{ s.step }}</span>
          <span class="text-white/50 text-xs font-mono truncate flex-1">{{ s.output }}</span>
        </div>
      </div>
      <div v-if="deployError" class="mt-2 text-sm text-red-400">{{ deployError }}</div>
      <div v-if="deploySuccess" class="mt-2 text-sm text-green-400">✅ 部署完成！</div>
    </div>

    <!-- Deploy History -->
    <div class="glass rounded-xl p-5">
      <h3 class="font-semibold text-cyan-300 mb-3">📋 部署歷史</h3>
      <div v-if="!history.length" class="text-white/50 text-sm">尚無部署紀錄</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead><tr class="bg-ocean-800/60">
            <th class="text-left px-4 py-2 font-semibold">時間</th>
            <th class="text-left px-4 py-2 font-semibold">操作者</th>
            <th class="text-left px-4 py-2 font-semibold">目標</th>
            <th class="text-left px-4 py-2 font-semibold">狀態</th>
            <th class="text-left px-4 py-2 font-semibold">訊息</th>
          </tr></thead>
          <tbody>
            <tr v-for="h in history" :key="h.ts + h.agent" class="border-t border-white/5">
              <td class="px-4 py-2 text-white/60 text-xs font-mono">{{ h.ts }}</td>
              <td class="px-4 py-2">{{ h.user }}</td>
              <td class="px-4 py-2 font-medium">{{ h.agent }}</td>
              <td class="px-4 py-2">
                <span :class="h.status === 'success' ? 'text-green-400' : 'text-red-400'">{{ h.status === 'success' ? '✅' : '❌' }} {{ h.status }}</span>
              </td>
              <td class="px-4 py-2 text-white/60 text-xs">{{ h.message }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, post } = useApi()

const git = ref({ branch: '', log: [], uncommitted: [] })
const history = ref([])
const agents = ref([
  { id: 'bob', name: '海綿寶寶' },
  { id: 'patrick', name: '派大星' },
  { id: 'pearl', name: '珍珍' },
  { id: 'larry', name: '蝦霸' },
  { id: 'squidward', name: '章魚哥' },
  { id: 'sandy', name: '珊迪' },
  { id: 'puff', name: '泡芙老師' },
  { id: 'conch', name: '神奇海螺' },
  { id: 'mermaid-man', name: '海超人' },
])
const deployTarget = ref('')
const deploying = ref(false)
const deploySteps = ref([])
const deployError = ref('')
const deploySuccess = ref(false)

async function loadAll() {
  const [gitRes, histRes] = await Promise.all([
    get('/api/deploy/git-status'),
    get('/api/deploy/history'),
  ])
  if (gitRes) git.value = gitRes
  if (histRes) history.value = histRes.history || []
}

async function doDeploy() {
  if (!deployTarget.value || deploying.value) return
  if (!confirm(`確定要部署 ${deployTarget.value}？（會觸發 build + restart）`)) return
  deploying.value = true
  deploySteps.value = []
  deployError.value = ''
  deploySuccess.value = false
  try {
    const res = await post(`/api/deploy/${deployTarget.value}`)
    if (res) {
      deploySteps.value = res.steps || []
      if (res.success) deploySuccess.value = true
      else deployError.value = res.error || '部署失敗'
    }
  } catch (e) {
    deployError.value = '網路錯誤'
  }
  deploying.value = false
  loadAll()
}

onMounted(loadAll)
</script>
