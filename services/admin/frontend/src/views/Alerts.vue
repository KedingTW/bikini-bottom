<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span>時間範圍：</span>
    <select v-model="days" @change="load()" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm">
      <option value="1">最近 1 天</option>
      <option value="7">最近 7 天</option>
      <option value="30">最近 30 天</option>
    </select>
    <span>角色：</span>
    <select v-model="agentFilter" @change="load()" class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm">
      <option value="">全部</option>
      <option v-for="a in agents" :key="a.name" :value="a.name">{{ a.display }}</option>
    </select>
    <span class="ml-auto text-white/70 text-xs">共 {{ alerts.length }} 筆紀錄</span>
  </div>

  <div class="p-7">
    <div v-if="!alerts.length" class="text-center py-16 text-white/60">🎉 目前沒有告警紀錄</div>

    <div v-else class="glass rounded-xl overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="bg-ocean-800/60">
            <th class="text-left px-5 py-3 text-sm font-semibold">時間</th>
            <th class="text-left px-5 py-3 text-sm font-semibold">等級</th>
            <th class="text-left px-5 py-3 text-sm font-semibold">角色</th>
            <th class="text-left px-5 py-3 text-sm font-semibold">訊息</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in alerts" :key="a.id" class="border-t border-white/5 hover:bg-white/5">
            <td class="px-5 py-3 text-sm">{{ fmtDate(a.ts) }}</td>
            <td class="px-5 py-3">
              <span class="text-xs px-2.5 py-1 rounded font-semibold"
                :class="a.level === 'critical' ? 'bg-red-500/25 text-red-300' : 'bg-yellow-500/25 text-yellow-300'">
                {{ a.level === 'critical' ? '嚴重' : '警告' }}
              </span>
            </td>
            <td class="px-5 py-3 text-sm">
              <div class="flex items-center gap-2">
                <img :src="'/avatar/' + a.agent" class="w-6 h-6 rounded-full object-cover" @error="$event.target.style.display='none'">
                <span>{{ getDisplay(a.agent) }}</span>
              </div>
            </td>
            <td class="px-5 py-3 text-sm">{{ a.message }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, post, pad } = useApi()

const agents = ref([])
const alerts = ref([])
const days = ref('7')
const agentFilter = ref('')

async function load() {
  const data = await get(`/api/alerts/history?days=${days.value}&agent=${agentFilter.value}`)
  alerts.value = data?.alerts || []
}

async function dismiss(id) {
  await post(`/api/alerts/${id}/dismiss`)
  load()
}

function getDisplay(name) {
  const a = agents.value.find(x => x.name === name)
  return a ? a.display : name
}

function fmtDate(ts) {
  const dt = new Date(ts + 'Z')
  return `${dt.getFullYear()}/${pad(dt.getMonth()+1)}/${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

onMounted(async () => {
  const sData = await get('/api/status')
  agents.value = sData?.agents || []
  load()
})
</script>
