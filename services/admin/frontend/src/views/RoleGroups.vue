<template>
  <div class="flex h-full">
    <!-- Left: Group list -->
    <div class="w-full md:w-64 shrink-0 md:border-r border-white/10 overflow-y-auto">
      <div class="p-3 border-b border-white/10 flex items-center justify-between">
        <h3 class="text-xs font-medium text-white/50 uppercase tracking-wider">角色組</h3>
        <button @click="openAdd()" class="text-xs px-2 py-1 rounded bg-cyan-600 text-white">+ 新增</button>
      </div>
      <div v-if="loading" class="p-4 text-center text-white/50 text-sm">載入中...</div>
      <div v-else class="py-1">
        <button v-for="g in groups" :key="g.id" @click="selectGroup(g)"
          class="w-full flex items-center gap-2.5 px-3 py-2.5 text-left transition"
          :class="selected?.id === g.id ? 'bg-cyan-500/15 border-l-2 border-cyan-400' : 'hover:bg-white/5 border-l-2 border-transparent'">
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium truncate" :class="selected?.id === g.id ? 'text-cyan-300' : 'text-white/90'">{{ g.name }}</div>
            <div class="text-[10px] text-white/50">{{ g.member_count }} 位成員</div>
          </div>
        </button>
      </div>
    </div>

    <!-- Right: Detail -->
    <div class="flex-1 overflow-y-auto p-4 sm:p-6" :class="selected ? '' : 'hidden md:block'">
      <button v-if="selected" @click="selected = null" class="md:hidden flex items-center gap-1 text-sm text-white/60 mb-4">← 返回</button>

      <div v-if="!selected" class="text-center py-20 text-white/50 hidden md:block">
        <div class="text-3xl mb-2">👥</div>
        <div>選擇角色組管理成員</div>
      </div>

      <div v-if="selected">
        <div class="flex items-center gap-3 mb-4">
          <h2 class="text-lg font-semibold">{{ selected.name }}</h2>
          <button @click="deleteGroup()" class="ml-auto text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10">🗑️ 刪除</button>
        </div>

        <!-- Description -->
        <div class="mb-4">
          <div class="text-xs text-white/50 mb-1">說明</div>
          <input v-model="desc" class="w-full bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400/50" placeholder="用途說明">
          <button @click="saveDesc()" class="mt-2 text-xs px-3 py-1 rounded bg-cyan-600 text-white">儲存說明</button>
        </div>

        <!-- Members -->
        <div class="text-sm text-white/60 mb-2">成員（勾選角色）</div>
        <div v-if="agentsLoading" class="text-sm text-white/40">載入中...</div>
        <div v-else class="space-y-1 mb-4">
          <label v-for="a in allAgents" :key="a.name" class="flex items-center gap-3 px-3 py-2 rounded hover:bg-white/5 cursor-pointer">
            <input type="checkbox" :value="a.name" v-model="members" class="w-4 h-4 accent-cyan-500">
            <img v-if="a.avatar_url" :src="a.avatar_url" class="w-6 h-6 rounded-full">
            <span class="text-sm text-white/90">{{ a.display }}</span>
          </label>
        </div>
        <button @click="saveMembers()" class="px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">💾 儲存成員</button>
        <span v-if="saveMsg" class="text-xs ml-2" :class="saveMsg.startsWith('✅') ? 'text-green-400' : 'text-red-400'">{{ saveMsg }}</span>

        <!-- Skills binding -->
        <div class="mt-6">
          <div class="text-sm text-white/60 mb-2">綁定技能</div>
          <div v-if="!allSkills.length" class="text-xs text-white/40">載入中...</div>
          <div v-else class="space-y-1 mb-3">
            <label v-for="s in allSkills" :key="s.name" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-white/5 cursor-pointer">
              <input type="checkbox" :value="s.name" v-model="boundSkills" class="w-4 h-4 accent-cyan-500">
              <span class="text-sm text-white/90">{{ s.display_name || s.name }}</span>
            </label>
          </div>
          <button @click="saveSkills()" class="px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">💾 儲存技能</button>
        </div>

        <!-- MCP binding -->
        <div class="mt-6">
          <div class="text-sm text-white/60 mb-2">綁定 MCP Server</div>
          <div v-if="!allMcpServers.length" class="text-xs text-white/40">載入中...</div>
          <div v-else class="space-y-1 mb-3">
            <label v-for="s in allMcpServers" :key="s.id" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-white/5 cursor-pointer">
              <input type="checkbox" :value="s.id" v-model="boundMcp" class="w-4 h-4 accent-cyan-500">
              <span class="text-sm text-white/90">{{ s.name }}</span>
            </label>
          </div>
          <button @click="saveMcp()" class="px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">💾 儲存 MCP</button>
        </div>
      </div>
    </div>

    <!-- Add Dialog -->
    <div v-if="addDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="addDialog = false">
      <div class="bg-ocean-700 rounded-xl w-full max-w-sm p-6 shadow-2xl border border-white/10">
        <h3 class="text-lg font-semibold mb-4">新增角色組</h3>
        <input v-model="addName" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none focus:border-cyan-400/60 mb-3" placeholder="角色組名稱">
        <div class="flex gap-3 justify-end">
          <button @click="addDialog = false" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70">取消</button>
          <button @click="doAdd()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 text-white">新增</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, post, put } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const groups = ref([])
const loading = ref(false)
const selected = ref(null)
const members = ref([])
const desc = ref('')
const allAgents = ref([])
const agentsLoading = ref(false)
const addDialog = ref(false)
const addName = ref('')
const saveMsg = ref('')
const allSkills = ref([])
const allMcpServers = ref([])
const boundSkills = ref([])
const boundMcp = ref([])

async function load() {
  loading.value = true
  const res = await get('/api/role-groups')
  groups.value = res?.groups || []
  loading.value = false
}

async function loadAgents() {
  agentsLoading.value = true
  const res = await get(`/api/agents?group=${currentGroup.value}`)
  allAgents.value = res?.agents || []
  agentsLoading.value = false
}

async function loadSkillsAndMcp() {
  if (!allSkills.value.length) {
    const res = await get('/api/skills')
    allSkills.value = res?.skills || []
  }
  if (!allMcpServers.value.length) {
    const res = await get('/api/mcp-servers')
    allMcpServers.value = res?.servers || []
  }
}

async function saveSkills() {
  const res = await put(`/api/role-groups/${selected.value.id}/skills`, { skills: boundSkills.value })
  if (res?.ok) { saveMsg.value = '✅'; setTimeout(() => { saveMsg.value = '' }, 2000) }
}

async function saveMcp() {
  const res = await put(`/api/role-groups/${selected.value.id}/mcp`, { servers: boundMcp.value })
  if (res?.ok) { saveMsg.value = '✅'; setTimeout(() => { saveMsg.value = '' }, 2000) }
}

async function selectGroup(g) {
  selected.value = g
  desc.value = g.description || ''
  const res = await get(`/api/role-groups/${g.id}/members`)
  members.value = res?.members || []
  if (!allAgents.value.length) loadAgents()
  loadSkillsAndMcp()
  const skillRes = await get(`/api/role-groups/${g.id}/skills`)
  boundSkills.value = skillRes?.skills || []
  const mcpRes = await get(`/api/role-groups/${g.id}/mcp`)
  boundMcp.value = mcpRes?.servers || []
}

async function saveDesc() {
  await put(`/api/role-groups/${selected.value.id}`, { name: selected.value.name, description: desc.value })
  selected.value.description = desc.value
}

async function saveMembers() {
  saveMsg.value = ''
  const res = await put(`/api/role-groups/${selected.value.id}/members`, { members: members.value })
  if (res?.ok) { saveMsg.value = '✅'; setTimeout(() => { saveMsg.value = '' }, 2000); load() }
  else { saveMsg.value = '❌ 儲存失敗' }
}

async function deleteGroup() {
  if (!confirm(`確定刪除「${selected.value.name}」？`)) return
  await fetch(`/api/role-groups/${selected.value.id}`, { method: 'DELETE' })
  selected.value = null
  load()
}

function openAdd() { addDialog.value = true; addName.value = '' }
async function doAdd() {
  if (!addName.value.trim()) return
  await post('/api/role-groups', { name: addName.value.trim() })
  addDialog.value = false
  load()
}

onMounted(load)
</script>
