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
          <button @click="deleteGroup()" class="text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10">🗑️ 刪除</button>
          <button @click="saveAll()" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">💾 儲存</button>
          <span v-if="saveMsg" class="text-xs" :class="saveMsg.startsWith('✅') ? 'text-green-400' : 'text-red-400'">{{ saveMsg }}</span>
        </div>

        <!-- Description -->
        <div class="mb-5">
          <div class="text-xs text-white/50 mb-1">說明</div>
          <input v-model="desc" class="w-full bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400/50" placeholder="用途說明">
        </div>

        <!-- Members -->
        <div class="mb-5">
          <div class="text-sm text-white/60 mb-2">成員</div>
          <div v-if="agentsLoading" class="text-xs text-white/40">載入中...</div>
          <div v-else class="space-y-1">
            <label v-for="a in allAgents" :key="a.name" class="flex items-center gap-3 px-3 py-2 rounded hover:bg-white/5 cursor-pointer">
              <input type="checkbox" :value="a.name" v-model="members" class="w-4 h-4 accent-cyan-500">
              <img v-if="a.avatar_url" :src="a.avatar_url" class="w-6 h-6 rounded-full">
              <span class="text-sm text-white/90">{{ a.display }}</span>
            </label>
          </div>
        </div>

        <!-- Skills -->
        <div class="mb-5">
          <div class="text-sm text-white/60 mb-1">綁定技能</div>
          <div class="text-[10px] text-white/30 mb-2">模板配置（招募臨時角色時套用）</div>
          <div v-if="!allSkills.length" class="text-xs text-white/40">載入中...</div>
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-1">
            <label v-for="s in allSkills" :key="s.name" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-white/5 cursor-pointer">
              <input type="checkbox" :value="s.name" v-model="boundSkills" class="w-4 h-4 accent-cyan-500">
              <span class="text-sm" :class="boundSkills.includes(s.name) ? 'text-white/90' : 'text-white/40'">{{ s.display_name || s.name }}</span>
            </label>
          </div>
        </div>

        <!-- MCP -->
        <div class="mb-5">
          <div class="text-sm text-white/60 mb-1">綁定 MCP Server</div>
          <div class="text-[10px] text-white/30 mb-2">模板配置（招募臨時角色時套用）</div>
          <div v-if="!allMcpServers.length" class="text-xs text-white/40">載入中...</div>
          <div v-else class="space-y-2">
            <div v-for="s in allMcpServers" :key="s.id" class="bg-ocean-700/50 rounded-lg overflow-hidden">
              <div class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-white/5" @click="toggleMcpExpand(s)">
                <input type="checkbox" :checked="isMcpEnabled(s.id)" @click.stop="toggleMcpServer(s)" class="w-4 h-4 accent-cyan-500">
                <span class="text-sm flex-1" :class="isMcpEnabled(s.id) ? 'text-cyan-300' : 'text-white/40'">{{ s.name }}</span>
                <span class="text-[10px] text-white/30">{{ getMcpToolCount(s.id) }}/{{ (s.tools || []).length }}</span>
                <span class="text-xs text-white/30">{{ s._open ? '▼' : '▶' }}</span>
              </div>
              <div v-if="s._open && isMcpEnabled(s.id)" class="px-3 pb-2 border-t border-white/5">
                <div class="flex gap-2 py-1.5 mb-1">
                  <button @click="mcpSelectAll(s)" type="button" class="text-[10px] px-2 py-0.5 rounded bg-cyan-600/20 text-cyan-300">全選</button>
                  <button @click="mcpDeselectAll(s)" type="button" class="text-[10px] px-2 py-0.5 rounded bg-white/10 text-white/60">取消</button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-0.5">
                  <label v-for="t in (s.tools || [])" :key="t" class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-white/5 cursor-pointer text-xs">
                    <input type="checkbox" :checked="isMcpToolEnabled(s.id, t)" @change="toggleMcpTool(s.id, t)" class="w-3 h-3 accent-cyan-500">
                    <span :class="isMcpToolEnabled(s.id, t) ? 'text-white/90' : 'text-white/40'">{{ t }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
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
const boundMcp = ref({})  // { server_id: [enabled_tools] or 'all' }

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
    allMcpServers.value = (res?.servers || []).map(s => ({ ...s, _open: false }))
    // Load tools for each server
    for (const s of allMcpServers.value) {
      const detail = await get(`/api/mcp-servers/${s.id}`)
      if (detail?.tools) s.tools = detail.tools.map(t => typeof t === 'string' ? t : t.name || t.tool_name)
    }
  }
}

function isMcpEnabled(sid) { return sid in boundMcp.value }
function getMcpToolCount(sid) {
  if (!boundMcp.value[sid]) return 0
  return boundMcp.value[sid] === 'all' ? (allMcpServers.value.find(s => s.id === sid)?.tools || []).length : boundMcp.value[sid].length
}
function toggleMcpServer(s) {
  if (isMcpEnabled(s.id)) { delete boundMcp.value[s.id] }
  else { boundMcp.value[s.id] = 'all' }
}
function toggleMcpExpand(s) { s._open = !s._open }
function isMcpToolEnabled(sid, tool) {
  if (!boundMcp.value[sid]) return false
  if (boundMcp.value[sid] === 'all') return true
  return boundMcp.value[sid].includes(tool)
}
function toggleMcpTool(sid, tool) {
  const server = allMcpServers.value.find(s => s.id === sid)
  const allTools = server?.tools || []
  if (boundMcp.value[sid] === 'all') {
    boundMcp.value[sid] = allTools.filter(t => t !== tool)
  } else {
    const arr = boundMcp.value[sid] || []
    if (arr.includes(tool)) { boundMcp.value[sid] = arr.filter(t => t !== tool) }
    else { boundMcp.value[sid] = [...arr, tool] }
    if (boundMcp.value[sid].length >= allTools.length) boundMcp.value[sid] = 'all'
  }
  if (Array.isArray(boundMcp.value[sid]) && boundMcp.value[sid].length === 0) delete boundMcp.value[sid]
}
function mcpSelectAll(s) { boundMcp.value[s.id] = 'all' }
function mcpDeselectAll(s) { delete boundMcp.value[s.id] }

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
  // Convert to object: each enabled server = 'all' (for now)
  boundMcp.value = {}
  for (const sid of (mcpRes?.servers || [])) { boundMcp.value[sid] = 'all' }
}

async function saveAll() {
  saveMsg.value = ''
  await put(`/api/role-groups/${selected.value.id}`, { name: selected.value.name, description: desc.value })
  await put(`/api/role-groups/${selected.value.id}/members`, { members: members.value })
  await put(`/api/role-groups/${selected.value.id}/skills`, { skills: boundSkills.value })
  await put(`/api/role-groups/${selected.value.id}/mcp`, { servers: Object.keys(boundMcp.value).map(Number) })
  saveMsg.value = '✅'
  setTimeout(() => { saveMsg.value = '' }, 2000)
  load()
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
