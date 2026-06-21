<template>
  <div class="p-4 sm:p-6">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5 flex-wrap">
      <h2 class="text-lg font-semibold">MCP Servers Pool</h2>
      <span class="text-xs text-white/50">{{ servers.length }} 個 server</span>
      <button @click="openAdd()" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">+ 新增 Server</button>
    </div>

    <!-- Server List (mobile: full width cards) -->
    <div v-if="loading" class="text-center py-10 text-white/50">載入中...</div>
    <div v-else-if="!servers.length" class="text-center py-20 text-white/50">
      <div class="text-3xl mb-2">📭</div>
      <div>尚未建立任何 MCP Server</div>
    </div>
    <div v-else class="space-y-3">
      <div v-for="s in servers" :key="s.id" class="bg-ocean-800/50 rounded-lg border border-white/5 overflow-hidden">
        <!-- Server row -->
        <div class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/5" @click="toggleExpand(s.id)">
          <span class="text-cyan-400 text-lg">🔌</span>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-sm text-cyan-300">{{ s.name }}</div>
            <div class="text-[11px] text-white/50 truncate">{{ s.path }} · {{ s.description }}</div>
          </div>
          <span class="text-xs text-white/40 bg-ocean-700 px-2 py-0.5 rounded">{{ s.tool_count }} tools</span>
          <div class="flex gap-1">
            <button @click.stop="openEdit(s)" class="text-xs px-2 py-1 rounded border border-white/15 hover:bg-white/10">✏️</button>
            <button @click.stop="del_server(s)" class="text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10">🗑️</button>
          </div>
          <span class="text-xs text-white/30">{{ expanded === s.id ? '▼' : '▶' }}</span>
        </div>
        <!-- Tools detail -->
        <div v-if="expanded === s.id" class="px-4 pb-4 border-t border-white/5">
          <div v-if="detailLoading" class="py-3 text-white/50 text-xs">載入 tools...</div>
          <template v-else>
            <div class="flex items-center gap-2 py-2 mb-1">
              <span class="text-xs text-white/50">Tools</span>
              <button @click="showAddTool = s.id" class="ml-auto text-[10px] px-2 py-0.5 rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30">+ 新增 Tool</button>
            </div>
            <div v-if="!detail?.tools?.length" class="text-xs text-white/40 py-2">無 tools</div>
            <div v-else class="flex flex-wrap gap-1.5">
              <span v-for="t in detail.tools" :key="t.id" class="inline-flex items-center gap-1 text-xs bg-ocean-700 px-2 py-1 rounded text-white/80">
                {{ t.name }}
                <button @click="delTool(s.id, t.id)" class="text-red-400/60 hover:text-red-400 ml-0.5">×</button>
              </span>
            </div>
            <!-- Add tool inline -->
            <div v-if="showAddTool === s.id" class="mt-3 flex gap-2">
              <input v-model="newToolName" placeholder="Tool 名稱" class="flex-1 bg-ocean-800 border border-white/15 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-cyan-400/60">
              <button @click="addTool(s.id)" class="px-3 py-1 text-xs rounded bg-cyan-600 text-white">新增</button>
              <button @click="showAddTool = null; newToolName = ''" class="px-2 py-1 text-xs text-white/50">取消</button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Add/Edit Server Dialog -->
    <div v-if="dialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="dialog = null">
      <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
        <h3 class="text-lg font-semibold mb-4">{{ dialog.mode === 'add' ? '新增' : '編輯' }} MCP Server</h3>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">名稱</label>
          <input v-model="dialog.name" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none focus:border-cyan-400/60" placeholder="e.g. hrs-mcp">
        </div>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">Path</label>
          <input v-model="dialog.path" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono focus:outline-none focus:border-cyan-400/60" placeholder="/mcp/hrs">
        </div>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1">說明</label>
          <input v-model="dialog.description" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none focus:border-cyan-400/60" placeholder="選填">
        </div>
        <div v-if="dialog.error" class="mb-3 text-sm text-red-400">{{ dialog.error }}</div>
        <div class="flex gap-3 justify-end">
          <button @click="dialog = null" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
          <button @click="saveDialog()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">
            {{ dialog.mode === 'add' ? '新增' : '儲存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, post, put } = useApi()

const servers = ref([])
const loading = ref(false)
const expanded = ref(null)
const detail = ref(null)
const detailLoading = ref(false)
const dialog = ref(null)
const showAddTool = ref(null)
const newToolName = ref('')

async function load() {
  loading.value = true
  const res = await get('/api/mcp-servers')
  servers.value = res?.servers || []
  loading.value = false
}

async function toggleExpand(id) {
  if (expanded.value === id) { expanded.value = null; return }
  expanded.value = id
  detailLoading.value = true
  const res = await get(`/api/mcp-servers/${id}`)
  detail.value = res
  detailLoading.value = false
}

function openAdd() {
  dialog.value = { mode: 'add', name: '', path: '', description: '', error: '' }
}

function openEdit(s) {
  dialog.value = { mode: 'edit', id: s.id, name: s.name, path: s.path, description: s.description || '', error: '' }
}

async function saveDialog() {
  const d = dialog.value
  if (!d.name || !d.path) { d.error = 'name 和 path 為必填'; return }
  let res
  if (d.mode === 'add') {
    res = await post('/api/mcp-servers', { name: d.name, path: d.path, description: d.description })
  } else {
    res = await put(`/api/mcp-servers/${d.id}`, { name: d.name, path: d.path, description: d.description })
  }
  if (res?.ok) { dialog.value = null; load() }
  else { d.error = res?.detail || '操作失敗' }
}

async function del_server(s) {
  if (!confirm(`確定刪除 ${s.name}？所有相關 tools 和角色配置都會一併刪除。`)) return
  const res = await fetch(`/api/mcp-servers/${s.id}`, { method: 'DELETE' })
  if (res.ok) load()
}

async function addTool(serverId) {
  if (!newToolName.value.trim()) return
  await post(`/api/mcp-servers/${serverId}/tools`, { name: newToolName.value.trim() })
  newToolName.value = ''
  showAddTool.value = null
  // Refresh detail
  const res = await get(`/api/mcp-servers/${serverId}`)
  detail.value = res
  load()
}

async function delTool(serverId, toolId) {
  await fetch(`/api/mcp-servers/${serverId}/tools/${toolId}`, { method: 'DELETE' })
  const res = await get(`/api/mcp-servers/${serverId}`)
  detail.value = res
  load()
}

onMounted(load)
</script>
