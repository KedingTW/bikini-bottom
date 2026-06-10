<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm sticky top-0 z-10">
    <span class="font-medium">MCP 管理</span>
    <span class="text-white/40 text-xs">{{ servers.length }} 個 Server</span>
    <button @click="showAdd = true" class="ml-auto bg-cyan-600 hover:bg-cyan-500 text-white rounded px-3 py-1.5 text-sm">+ 新增</button>
  </div>

  <div class="p-7">
    <!-- Tag Filter -->
    <div v-if="allTags.length" class="flex gap-2 mb-4 flex-wrap">
      <button @click="tagFilter = ''" :class="!tagFilter ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-2.5 py-1 rounded text-xs">全部</button>
      <button v-for="t in allTags" :key="t" @click="tagFilter = t" :class="tagFilter === t ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-2.5 py-1 rounded text-xs">{{ t }}</button>
    </div>

    <!-- Server List -->
    <div class="space-y-3">
      <div v-for="s in filteredServers" :key="s.id" class="glass rounded-xl p-5">
        <div class="flex items-center gap-3 mb-3">
          <span class="font-medium text-base" :class="s.disabled ? 'text-white/40 line-through' : 'text-cyan-300'">{{ s.name }}</span>
          <span class="text-xs font-mono text-white/40">{{ s.key }}</span>
          <span v-if="s.tags" class="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">{{ s.tags }}</span>
          <span :class="s.disabled ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'" class="text-xs px-2 py-0.5 rounded">{{ s.disabled ? '停用' : '啟用' }}</span>
          <div class="ml-auto flex gap-2">
            <button @click="editServer(s)" class="text-xs px-2.5 py-1 rounded border border-white/20 hover:bg-white/10">✏️ 編輯</button>
            <button @click="deleteServer(s.id)" class="text-xs px-2.5 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10">刪除</button>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
          <div><span class="text-white/50">URL:</span> <span class="font-mono ml-1">{{ s.url }}</span></div>
          <div><span class="text-white/50">Headers:</span> <span class="font-mono ml-1 text-white/40">{{ maskHeaders(s.headers) }}</span></div>
          <div class="col-span-2" v-if="s.available_tools.length"><span class="text-white/50">Tools:</span> <span class="ml-1">{{ s.available_tools.length }} 個</span></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Add/Edit Dialog -->
  <div v-if="showAdd || editingServer" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="closeForm()">
    <div class="bg-ocean-700 rounded-xl w-full max-w-lg p-6 shadow-2xl">
      <h3 class="font-semibold text-lg mb-4">{{ editingServer ? '編輯 MCP Server' : '新增 MCP Server' }}</h3>
      <div class="space-y-3">
        <div><label class="text-sm text-white/70">Key（唯一識別碼）</label><input v-model="form.key" :disabled="!!editingServer" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm font-mono text-white" placeholder="例：als-mcp"></div>
        <div><label class="text-sm text-white/70">名稱</label><input v-model="form.name" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm text-white" placeholder="例：ALS 後勤系統"></div>
        <div><label class="text-sm text-white/70">URL</label><input v-model="form.url" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm font-mono text-white" placeholder="http://..."></div>
        <div><label class="text-sm text-white/70">Headers（JSON）</label><input v-model="form.headersStr" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm font-mono text-white" placeholder='{"Authorization": "Bearer xxx"}'></div>
        <div><label class="text-sm text-white/70">標籤</label><input v-model="form.tags" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm text-white" placeholder="正式、測試、客訴相關"></div>
        <div><label class="text-sm text-white/70">可用 Tools（逗號分隔）</label><input v-model="form.toolsStr" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm font-mono text-white" placeholder="Tool1, Tool2"></div>
      </div>
      <div class="flex items-center gap-3 mt-5">
        <button @click="submitForm()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-5 py-2 rounded text-sm font-medium">{{ editingServer ? '更新' : '建立' }}</button>
        <button @click="closeForm()" class="text-white/60 text-sm">取消</button>
        <span v-if="formError" class="text-red-400 text-sm ml-2">{{ formError }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'
const { get, post, put } = useApi()

const servers = ref([])
const tagFilter = ref('')
const showAdd = ref(false)
const editingServer = ref(null)
const form = ref({ key: '', name: '', url: '', headersStr: '{}', tags: '', toolsStr: '' })
const formError = ref('')

const allTags = computed(() => [...new Set(servers.value.map(s => s.tags).filter(Boolean))])
const filteredServers = computed(() => tagFilter.value ? servers.value.filter(s => s.tags === tagFilter.value) : servers.value)

function maskHeaders(h) {
  if (!h || !Object.keys(h).length) return '（無）'
  return Object.entries(h).map(([k, v]) => `${k}: ${String(v).slice(0, 4)}***`).join(', ')
}

async function load() {
  const res = await get('/api/mcp-registry')
  servers.value = res?.servers || []
}

function editServer(s) {
  editingServer.value = s
  form.value = { key: s.key, name: s.name, url: s.url, headersStr: JSON.stringify(s.headers), tags: s.tags, toolsStr: s.available_tools.join(', ') }
}

function closeForm() { showAdd.value = false; editingServer.value = null; formError.value = '' }

async function submitForm() {
  formError.value = ''
  let headers = {}
  try { headers = JSON.parse(form.value.headersStr || '{}') } catch { formError.value = 'Headers JSON 格式錯誤'; return }
  const tools = form.value.toolsStr ? form.value.toolsStr.split(',').map(t => t.trim()).filter(Boolean) : []
  const payload = { key: form.value.key, name: form.value.name, url: form.value.url, headers, available_tools: tools, tags: form.value.tags }
  if (editingServer.value) {
    await put(`/api/mcp-registry/${editingServer.value.id}`, payload)
  } else {
    const res = await post('/api/mcp-registry', payload)
    if (res?.detail) { formError.value = res.detail; return }
  }
  closeForm()
  load()
}

async function deleteServer(id) {
  if (!confirm('確定刪除？')) return
  await fetch(`/api/mcp-registry/${id}`, { method: 'DELETE', credentials: 'same-origin' })
  load()
}

onMounted(load)
</script>
