<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <div class="flex gap-1 bg-ocean-800/50 rounded-lg p-1">
      <button v-for="t in tabs" :key="t.key" @click="activeTab = t.key"
        :class="activeTab === t.key ? 'bg-cyan-600 text-white' : 'text-white/60 hover:text-white'"
        class="px-4 py-1.5 rounded-md text-sm font-medium transition">{{ t.label }}</button>
    </div>
    <button @click="refresh()" class="ml-auto bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </div>

  <div class="p-7">
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-4"></div>
    </div>

    <!-- Members -->
    <div v-if="!loading && activeTab === 'members'">
      <div class="mb-4 flex items-center gap-3">
        <input v-model="search" placeholder="搜尋成員..." class="bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm w-64 focus:outline-none focus:border-cyan-400/60">
        <span class="text-white/50 text-xs">共 {{ filteredMembers.length }} 人</span>
      </div>
      <div class="glass rounded-xl overflow-hidden">
        <table class="w-full">
          <thead><tr class="bg-ocean-800/60">
            <th class="text-left px-5 py-2 text-sm font-semibold">成員</th>
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

    <!-- Roles -->
    <div v-if="!loading && activeTab === 'roles'">
      <div v-if="!roles.length" class="text-center py-12 text-white/50">此伺服器尚無身分組</div>
      <div v-else class="space-y-4">
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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useApi } from '../composables/useApi.js'
const { get } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const activeTab = ref('members')
const loading = ref(false)
const members = ref([])
const roles = ref([])
const search = ref('')
const tabs = [{ key: 'members', label: '👥 成員' }, { key: 'roles', label: '🎭 身分組' }]

const filteredMembers = computed(() => {
  if (!search.value) return members.value
  const q = search.value.toLowerCase()
  return members.value.filter(m => m.display_name.toLowerCase().includes(q) || m.username.toLowerCase().includes(q))
})

function getRoleName(id) { return roles.value.find(r => r.id === id)?.name || id }
function getRoleColor(id) { const r = roles.value.find(r => r.id === id); return r?.color ? '#' + r.color.toString(16).padStart(6,'0') : '#aaa' }
function getRoleMembers(roleId) { return members.value.filter(m => m.roles.includes(roleId)) }
function formatDate(iso) { if (!iso) return '-'; const d = new Date(iso); return `${d.getFullYear()}/${String(d.getMonth()+1).padStart(2,'0')}/${String(d.getDate()).padStart(2,'0')}` }

async function refresh() {
  loading.value = true
  const [mRes, rRes] = await Promise.all([get(`/api/discord/members?group=${currentGroup.value}`), get(`/api/discord/roles?group=${currentGroup.value}`)])
  members.value = mRes?.members || []; roles.value = rRes?.roles || []
  loading.value = false
}

onMounted(() => {
  refresh()
  window.addEventListener('group-changed', refresh)
})
</script>
