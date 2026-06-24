<template>
  <div class="p-4 sm:p-6">
    <div class="flex items-center gap-3 mb-5 flex-wrap">
      <h2 class="text-lg font-semibold">MCP Servers</h2>
      <span class="text-xs text-white/50">{{ servers.length }} 個 server</span>
      <button @click="openAdd()" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">+ 新增 MCP Server</button>
    </div>

    <div v-if="loading" class="text-center py-10 text-white/50">載入中...</div>
    <div v-else-if="!servers.length" class="text-center py-20 text-white/50">
      <div class="text-3xl mb-2">📭</div>
      <div>尚未建立任何 MCP Server</div>
    </div>
    <div v-else class="space-y-3">
      <div v-for="s in servers" :key="s.id" class="bg-ocean-800/50 rounded-lg border border-white/5 p-4">
        <div class="flex items-center gap-3">
          <span class="text-lg">{{ s.type === 'remote' ? '🌐' : '💻' }}</span>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-sm text-cyan-300">{{ s.name }}</div>
            <div class="text-[11px] text-white/50 truncate">{{ s.type === 'remote' ? s.url : s.command }} · {{ s.description || '無說明' }}</div>
          </div>
          <span class="text-[10px] px-2 py-0.5 rounded bg-ocean-700 text-white/60">{{ s.type === 'remote' ? '遠端' : '本地' }}</span>
          <span v-if="s.tool_count" class="text-[10px] px-2 py-0.5 rounded bg-cyan-600/20 text-cyan-300">{{ s.tool_count }} tools</span>
          <button @click="openEdit(s)" class="text-xs px-2 py-1 rounded border border-white/15 hover:bg-white/10">✏️ 編輯</button>
          <button @click="del_server(s)" class="text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10">🗑️ 刪除</button>
        </div>
      </div>
    </div>

    <!-- Dialog -->
    <div v-if="dialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="dialog = null">
      <div class="bg-ocean-700 rounded-xl w-full max-w-lg p-6 shadow-2xl border border-white/10 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">{{ dialog.mode === 'add' ? '新增' : '編輯' }} MCP Server</h3>

        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">名稱 <span class="text-red-400">*</span></label>
          <input v-model="dialog.name" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none focus:border-cyan-400/60" placeholder="e.g. hrs-mcp">
        </div>

        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">連線方式</label>
          <select v-model="dialog.type" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none">
            <option value="remote">Remote（Streamable HTTP / SSE）</option>
            <option value="stdio">Stdio（本地指令）</option>
          </select>
        </div>

        <div v-if="dialog.type === 'remote'" class="mb-3">
          <label class="block text-sm text-white/70 mb-1">URL <span class="text-red-400">*</span></label>
          <input v-model="dialog.url" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono focus:outline-none focus:border-cyan-400/60" placeholder="https://mcp.example.com/mcp/hrs">
        </div>

        <div v-if="dialog.type === 'remote'" class="mb-3">
          <label class="block text-sm text-white/70 mb-1">Headers</label>
          <div class="space-y-2">
            <div v-for="(h, i) in dialog.headers" :key="i" class="flex gap-2 items-center">
              <input v-model="h.key" class="w-1/3 px-2 py-1.5 rounded bg-ocean-800 border border-white/20 text-white text-xs font-mono focus:outline-none focus:border-cyan-400/60" placeholder="Key">
              <input v-model="h.value" class="flex-1 px-2 py-1.5 rounded bg-ocean-800 border border-white/20 text-white text-xs font-mono focus:outline-none focus:border-cyan-400/60" placeholder="Value">
              <button @click="dialog.headers.splice(i, 1)" type="button" class="text-red-400/60 hover:text-red-400 shrink-0">✕</button>
            </div>
          </div>
          <button @click="dialog.headers.push({ key: '', value: '' })" type="button" class="mt-2 text-xs text-cyan-400 hover:underline">+ 新增 Header</button>
        </div>

        <div v-if="dialog.type === 'stdio'" class="space-y-3 mb-3">
          <div>
            <label class="block text-sm text-white/70 mb-1">Command <span class="text-red-400">*</span></label>
            <input v-model="dialog.command" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono focus:outline-none focus:border-cyan-400/60" placeholder="npx">
          </div>
          <div>
            <label class="block text-sm text-white/70 mb-1">Args（每行一個）</label>
            <textarea v-model="dialog.argsText" rows="3" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-xs font-mono focus:outline-none focus:border-cyan-400/60" placeholder="-y&#10;@modelcontextprotocol/server-example"></textarea>
          </div>
        </div>

        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">說明</label>
          <input v-model="dialog.description" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none focus:border-cyan-400/60" placeholder="選填">
        </div>

        <!-- Test result + tools display -->
        <div v-if="testLoading" class="mb-3 text-sm text-white/40 text-center py-2">連線測試中...</div>
        <div v-if="testResult === false" class="mb-3 text-sm text-red-400">❌ {{ testError }}</div>
        <div v-if="testResult === true && dialog.tools && dialog.tools.length" class="mb-4">
          <div class="text-sm text-green-400 mb-2">✅ 連線成功，偵測到 {{ dialog.tools.length }} 個 tools：</div>
          <div class="flex flex-wrap gap-2">
            <span v-for="t in dialog.tools" :key="t" class="text-sm bg-cyan-600/15 text-cyan-300 px-2 py-1 rounded">{{ t }}</span>
          </div>
        </div>

        <div v-if="dialog.error" class="mb-3 text-sm text-red-400">{{ dialog.error }}</div>
        <div class="flex gap-3 justify-end">
          <button @click="dialog = null" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
          <button v-if="dialog.type !== 'remote' || testResult === true" @click="saveDialog()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">
            💾 {{ dialog.mode === 'add' ? '新增' : '儲存' }}
          </button>
          <button v-else @click="testConnection()" :disabled="!dialog.url.trim() || testLoading" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium disabled:opacity-40">
            🔗 測試連線
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
const dialog = ref(null)
const testLoading = ref(false)
const testResult = ref(null)
const testError = ref('')

async function load() {
  loading.value = true
  const res = await get('/api/mcp-servers')
  servers.value = res?.servers || []
  loading.value = false
}

async function testConnection() {
  if (!dialog.value?.url.trim()) return
  testLoading.value = true
  testResult.value = null
  testError.value = ''
  dialog.value.tools = []
  const headers = Object.fromEntries((dialog.value.headers || []).filter(h => h.key.trim()).map(h => [h.key.trim(), h.value]))
  try {
    const res = await post('/api/mcp-servers/test-connection', { url: dialog.value.url.trim(), headers })
    if (res?.ok) { testResult.value = true; dialog.value.tools = res.tools || [] }
    else { testResult.value = false; testError.value = res?.detail || res?.error || res?.message || '連線失敗' }
  } catch (e) { testResult.value = false; testError.value = String(e) }
  testLoading.value = false
}

function openAdd() {
  testResult.value = null; testError.value = ''
  dialog.value = {
    mode: 'add', name: '', type: 'remote', url: '', headers: [{ key: '', value: '' }], command: '', argsText: '',
    description: '', tools: [], error: ''
  }
}

function openEdit(s) {
  testResult.value = null; testError.value = ''
  dialog.value = {
    mode: 'edit', id: s.id, name: s.name, type: s.type,
    url: s.url || '', headers: Object.entries(s.headers || {}).map(([key, value]) => ({ key, value })),
    command: s.command || '', argsText: (s.args || []).join('\n'),
    description: s.description || '', tools: s.tools || [], error: ''
  }
}

function parseLines(text) { return text.split('\n').map(l => l.trim()).filter(Boolean) }
function parseJson(text, fallback) { if (!text.trim()) return fallback; try { return JSON.parse(text) } catch { return null } }

async function saveDialog() {
  const d = dialog.value
  if (!d.name.trim()) { d.error = 'name 為必填'; return }
  if (d.type === 'remote' && !d.url.trim()) { d.error = 'URL 為必填'; return }
  if (d.type === 'stdio' && !d.command.trim()) { d.error = 'Command 為必填'; return }

  const headers = Object.fromEntries((d.headers || []).filter(h => h.key.trim()).map(h => [h.key.trim(), h.value]))

  const payload = {
    name: d.name.trim(), type: d.type, url: d.url.trim(), headers: headers,
    command: d.command.trim(), args: parseLines(d.argsText),
    description: d.description.trim(), tools: d.tools || []
  }

  let res
  if (d.mode === 'add') res = await post('/api/mcp-servers', payload)
  else res = await put(`/api/mcp-servers/${d.id}`, payload)

  if (res?.ok) { dialog.value = null; load() }
  else { d.error = res?.detail || '操作失敗' }
}

async function del_server(s) {
  if (!confirm(`確定刪除 ${s.name}？相關角色配置會一併刪除。`)) return
  await fetch(`/api/mcp-servers/${s.id}`, { method: 'DELETE', credentials: 'same-origin' })
  load()
}

onMounted(load)
</script>
