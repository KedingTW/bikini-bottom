<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm sticky top-0 z-10">
    <span class="font-medium">MCP 管理</span>
    <span class="text-white/40 text-xs">{{ servers.length }} 個 Server</span>
    <span class="text-white/30 text-xs">ℹ️ 資料來源：mcp-configs/ 自動匯入</span>
    <button @click="showAdd = true" class="ml-auto bg-cyan-600 hover:bg-cyan-500 text-white rounded px-3 py-1.5 text-sm">+ 新增</button>
  </div>

  <div class="p-7">
    <!-- Tag Filter -->
    <div v-if="allTags.length" class="flex gap-2 mb-4 flex-wrap">
      <button @click="tagFilter = ''" :class="!tagFilter ? 'bg-cyan-600 text-white' : 'text-white/60 hover:text-white'" class="px-3 py-1 rounded text-sm">全部</button>
      <button v-for="t in allTags" :key="t" @click="tagFilter = t" :class="tagFilter === t ? 'bg-cyan-600 text-white' : 'text-white/60 hover:text-white'" class="px-3 py-1 rounded text-sm">{{ t }}</button>
    </div>

    <!-- Server List -->
    <div class="space-y-3">
      <div v-for="s in filteredServers" :key="s.id" class="glass rounded-xl p-5">
        <div class="flex items-center gap-3 mb-3">
          <span class="font-bold text-base" :class="s.disabled ? 'text-white/40 line-through' : 'text-cyan-300'">{{ s.name }}</span>
          <span class="text-xs font-mono text-white/40 bg-ocean-800/50 px-2 py-0.5 rounded">{{ s.key }}</span>
          <span v-if="s.tags" class="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">{{ s.tags }}</span>
          <span :class="s.disabled ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'" class="text-xs px-2 py-0.5 rounded">{{ s.disabled ? '停用' : '啟用' }}</span>
          <div class="ml-auto flex gap-2">
            <button @click="testServer(s)" class="text-xs px-3 py-1.5 rounded border border-white/20 hover:bg-white/10">🔗 測試</button>
            <button @click="editServer(s)" class="text-xs px-3 py-1.5 rounded border border-white/20 hover:bg-white/10">✏️ 編輯</button>
            <button @click="deleteServer(s.id)" class="text-xs px-3 py-1.5 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10">刪除</button>
          </div>
        </div>
        <div v-if="testResults[s.id]" class="mb-2 text-xs" :class="testResults[s.id].ok ? 'text-green-400' : 'text-red-400'">
          {{ testResults[s.id].ok ? `✅ 連線成功（HTTP ${testResults[s.id].status}）` : `❌ ${testResults[s.id].error}` }}
        </div>
        <div class="space-y-2 text-sm">
          <div><span class="text-white/50 min-w-[60px] inline-block">URL</span><span class="font-mono">{{ s.url }}</span></div>
          <div v-if="s.headers && Object.keys(s.headers).length">
            <span class="text-white/50">Headers</span>
            <div class="ml-[60px] space-y-0.5">
              <div v-for="(v, k) in s.headers" :key="k" class="font-mono text-white/60"><span class="text-white/40">{{ k }}:</span> {{ maskVal(v) }}</div>
            </div>
          </div>
          <div v-if="s.available_tools.length"><span class="text-white/50">Tools</span><span class="ml-2 text-white/60">{{ s.available_tools.length }} 個</span></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Add/Edit Dialog -->
  <div v-if="showAdd || editingServer" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="closeForm()">
    <div class="bg-ocean-700 rounded-xl w-full max-w-lg p-6 shadow-2xl max-h-[85vh] overflow-y-auto">
      <h3 class="font-semibold text-lg mb-4">{{ editingServer ? '編輯 MCP Server' : '新增 MCP Server' }}</h3>
      <div class="space-y-3">
        <div><label class="text-sm text-white/70">Key（唯一識別碼）</label><input v-model="form.key" :disabled="!!editingServer" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm font-mono text-white" placeholder="例：als-mcp"></div>
        <div><label class="text-sm text-white/70">名稱</label><input v-model="form.name" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm text-white" placeholder="例：ALS 後勤系統"></div>
        <div><label class="text-sm text-white/70">連線方式</label>
          <select v-model="form.type" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm text-white">
            <option value="http">HTTP / SSE</option>
            <option value="stdio">Stdio</option>
          </select>
        </div>
        <div><label class="text-sm text-white/70">URL</label><input v-model="form.url" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm font-mono text-white" placeholder="http://..."></div>
        <div>
          <label class="text-sm text-white/70">Headers</label>
          <div class="mt-1 space-y-1">
            <div v-for="(h, i) in form.headers" :key="i" class="flex gap-2">
              <input v-model="h.key" placeholder="Key" class="flex-1 bg-ocean-800 border border-white/20 rounded px-2 py-1.5 text-sm font-mono text-white">
              <input v-model="h.value" placeholder="Value" class="flex-[2] bg-ocean-800 border border-white/20 rounded px-2 py-1.5 text-sm font-mono text-white">
              <button @click="form.headers.splice(i, 1)" class="text-red-400 text-xs px-2">✕</button>
            </div>
            <button @click="form.headers.push({key:'',value:''})" class="text-xs text-cyan-400 hover:text-cyan-300">+ Header</button>
          </div>
        </div>
        <div><label class="text-sm text-white/70">標籤（環境）</label>
          <select v-model="form.tags" class="w-full mt-1 bg-ocean-800 border border-white/20 rounded px-3 py-2 text-sm text-white">
            <option value="正式">正式</option>
            <option value="測試">測試</option>
            <option value="本地">本地</option>
          </select>
        </div>
        <div>
          <label class="text-sm text-white/70">可用 Tools</label>
          <div v-if="form.toolsList.length" class="mt-1 max-h-40 overflow-y-auto bg-ocean-800/50 rounded p-2 space-y-1">
            <label v-for="t in form.toolsList" :key="t" class="flex items-center gap-2 text-sm cursor-pointer hover:bg-white/5 px-2 py-1 rounded">
              <input type="checkbox" :value="t" v-model="form.selectedTools" class="w-3.5 h-3.5 rounded">
              <span class="font-mono text-xs">{{ t }}</span>
            </label>
          </div>
          <div v-else class="mt-1">
            <textarea v-model="form.toolsStr" rows="3" class="w-full bg-ocean-800 border border-white/20 rounded px-3 py-2 text-xs font-mono text-white" placeholder="每行一個 tool 名稱（無法自動取得時手動輸入）"></textarea>
            <div class="text-xs text-white/30 mt-1">無法連線 Server 時可手動輸入</div>
          </div>
        </div>
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
const form = ref({ key: '', name: '', type: 'http', url: '', headers: [{key:'',value:''}], tags: '正式', toolsStr: '', toolsList: [], selectedTools: [] })
const formError = ref('')
const testResults = ref({})

const allTags = computed(() => [...new Set(servers.value.map(s => s.tags).filter(Boolean))])
const filteredServers = computed(() => tagFilter.value ? servers.value.filter(s => s.tags === tagFilter.value) : servers.value)

function maskVal(v) { const s = String(v); return s.length > 8 ? s.slice(0,4) + '***' + s.slice(-4) : '***' }

async function load() {
  const res = await get('/api/mcp-registry')
  servers.value = res?.servers || []
}

function editServer(s) {
  editingServer.value = s
  const hdrs = Object.entries(s.headers || {}).map(([k,v]) => ({key:k, value:String(v)}))
  const tools = s.available_tools || []
  form.value = { key: s.key, name: s.name, type: 'http', url: s.url, headers: hdrs.length ? hdrs : [{key:'',value:''}], tags: s.tags || '正式', toolsStr: '', toolsList: tools, selectedTools: [...tools] }
}

function closeForm() { showAdd.value = false; editingServer.value = null; formError.value = ''; form.value = { key:'', name:'', type:'http', url:'', headers:[{key:'',value:''}], tags:'正式', toolsStr:'', toolsList:[], selectedTools:[] } }

async function submitForm() {
  formError.value = ''
  const headers = {}
  form.value.headers.forEach(h => { if (h.key.trim()) headers[h.key.trim()] = h.value })
  const tools = form.value.toolsList.length ? form.value.selectedTools : form.value.toolsStr.split('\n').map(t => t.trim()).filter(Boolean)
  const payload = { key: form.value.key, name: form.value.name, url: form.value.url, headers, available_tools: tools, tags: form.value.tags }
  if (editingServer.value) {
    await put(`/api/mcp-registry/${editingServer.value.id}`, payload)
  } else {
    const res = await post('/api/mcp-registry', payload)
    if (res?.detail) { formError.value = res.detail; return }
  }
  closeForm(); load()
}

async function reseed() {
  if (!confirm('重新匯入會清除現有資料，確定？')) return
  await post('/api/mcp-registry/reseed')
  load()
}

async function deleteServer(id) {
  if (!confirm('確定刪除？')) return
  await fetch(`/api/mcp-registry/${id}`, { method: 'DELETE', credentials: 'same-origin' })
  load()
}

async function testServer(s) {
  testResults.value = { ...testResults.value, [s.id]: null }
  const res = await post(`/api/mcp-registry/${s.id}/test`)
  testResults.value = { ...testResults.value, [s.id]: res }
}

onMounted(load)
</script>
