<template>
  <AgentDetailLayout :agents="agents" :selected-agent="selectedAgent" :loading="loading" @select="onSelect" @back="selectedAgent = null">
    <div v-if="!selectedAgent" class="text-center py-20 text-white/50 hidden md:block">
        <div class="text-3xl mb-2">🔌</div>
        <div>請選擇角色查看 MCP 配置</div>
      </div>

      <template v-else>
        <div class="flex items-center gap-3 mb-5 flex-wrap">
          <h2 class="text-lg font-semibold">{{ selectedAgent.display }} — MCP Servers</h2>
          <div class="flex gap-1 ml-auto">
            <button @click="mode = 'ui'" :class="mode === 'ui' ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-3 py-1 rounded text-xs">管理模式</button>
            <button @click="mode = 'raw'" :class="mode === 'raw' ? 'bg-cyan-600 text-white' : 'text-white/60'" class="px-3 py-1 rounded text-xs">JSON</button>
          </div>
          <button v-if="mode === 'ui'" @click="showAdd = true" class="text-xs px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white">+ 新增</button>
        </div>

        <!-- UI Mode -->
        <div v-if="mode === 'ui'" class="space-y-3">
          <div v-if="!servers.length" class="text-white/50 text-sm py-4">無 MCP Server 配置</div>
          <div v-for="name in servers" :key="name" class="bg-ocean-800/50 rounded-lg p-4">
            <div class="flex items-center gap-3 mb-3 flex-wrap">
              <span class="font-medium text-sm" :class="serversMap[name].disabled ? 'text-white/40 line-through' : 'text-cyan-300'">{{ name }}</span>
              <span v-if="serversMap[name].disabled" class="text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-300">停用</span>
              <span v-else class="text-xs px-1.5 py-0.5 rounded bg-green-500/20 text-green-300">啟用</span>
              <div class="ml-auto flex gap-2">
                <button @click="toggle(name)" class="text-xs px-2 py-1 rounded border border-white/20 hover:bg-white/10">{{ serversMap[name].disabled ? '啟用' : '停用' }}</button>
                <button @click="remove(name)" class="text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10">刪除</button>
              </div>
            </div>
            <div class="space-y-2">
              <div v-if="'url' in serversMap[name]" class="flex items-center gap-2">
                <span class="text-white/40 text-xs min-w-[50px]">url</span>
                <input :value="serversMap[name].url" @change="updateField(name, 'url', $event.target.value)"
                  class="flex-1 bg-ocean-800 text-white border border-white/10 rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-cyan-400/60">
              </div>
              <div v-if="serversMap[name].headers" class="flex items-start gap-2">
                <span class="text-white/40 text-xs min-w-[50px] mt-1">headers</span>
                <div class="flex-1 text-xs font-mono text-white/60">
                  <div v-for="(val, key) in serversMap[name].headers" :key="key" class="truncate">{{ key }}: {{ String(val).slice(0, 40) }}…</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Raw Mode -->
        <div v-if="mode === 'raw'">
          <textarea v-model="raw" rows="22" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-xs font-mono leading-relaxed resize-y"></textarea>
          <div class="flex items-center gap-3 mt-3">
            <button @click="save()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-1.5 rounded text-xs font-medium">💾 儲存</button>
            <span v-if="status" class="text-xs" :class="status.ok ? 'text-green-400' : 'text-red-400'">{{ status.text }}</span>
          </div>
        </div>
      </template>
    </div>

    <!-- Add Server Dialog -->
    <div v-if="showAdd" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showAdd = false">
      <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
        <h3 class="text-lg font-semibold mb-4">新增 MCP Server</h3>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">名稱</label>
          <input v-model="newSrv.name" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none focus:border-cyan-400/60" placeholder="e.g. my-server">
        </div>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">URL</label>
          <input v-model="newSrv.url" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono focus:outline-none focus:border-cyan-400/60" placeholder="http://...">
        </div>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">Headers（每行 key: value）</label>
          <textarea v-model="newSrv.headers" rows="3" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-xs font-mono focus:outline-none focus:border-cyan-400/60"></textarea>
        </div>
        <div class="flex gap-3 justify-end">
          <button @click="showAdd = false" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
          <button @click="addServer()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">新增</button>
        </div>
      </div>
    </div>
  </AgentDetailLayout>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAgentList } from '../composables/useAgentList.js'
import { useApi } from '../composables/useApi.js'
import AgentDetailLayout from '../components/AgentDetailLayout.vue'

const { get, put } = useApi()
const { agents, selectedAgent, loading, selectAgent } = useAgentList()

const mode = ref('ui')
const raw = ref('{}')
const status = ref(null)
const showAdd = ref(false)
const newSrv = ref({ name: '', url: '', headers: '' })

const serversMap = computed(() => { try { return JSON.parse(raw.value)?.mcpServers || {} } catch { return {} } })
const servers = computed(() => Object.keys(serversMap.value))

async function onSelect(a) {
  selectAgent(a)
  await loadMcp()
}

async function loadMcp() {
  if (!selectedAgent.value) return
  status.value = null
  const res = await get(`/api/agents/${selectedAgent.value.name}/mcp`)
  raw.value = res?.raw || '{}'
}

watch(selectedAgent, (a) => { if (a) loadMcp() })

async function save() {
  status.value = null
  try { JSON.parse(raw.value) } catch (e) { status.value = { ok: false, text: `❌ JSON 錯誤：${e.message}` }; return }
  const res = await put(`/api/agents/${selectedAgent.value.name}/mcp`, { raw: raw.value })
  status.value = res?.ok ? { ok: true, text: '✅ 已儲存' } : { ok: false, text: '❌ ' + (res?.detail || '失敗') }
}

function toggle(name) {
  try {
    const config = JSON.parse(raw.value)
    if (config.mcpServers?.[name]) { config.mcpServers[name].disabled = !config.mcpServers[name].disabled; raw.value = JSON.stringify(config, null, 2); save() }
  } catch {}
}

function updateField(name, field, value) {
  try {
    const config = JSON.parse(raw.value)
    if (config.mcpServers?.[name]) { config.mcpServers[name][field] = value; raw.value = JSON.stringify(config, null, 2); save() }
  } catch {}
}

function remove(name) {
  if (!confirm(`確定刪除「${name}」？`)) return
  try {
    const config = JSON.parse(raw.value)
    if (config.mcpServers) { delete config.mcpServers[name]; raw.value = JSON.stringify(config, null, 2); save() }
  } catch {}
}

function addServer() {
  if (!newSrv.value.name || !newSrv.value.url) return
  try {
    const config = JSON.parse(raw.value) || {}
    if (!config.mcpServers) config.mcpServers = {}
    const srv = { url: newSrv.value.url }
    const headers = {}
    newSrv.value.headers.split('\n').forEach(l => { const i = l.indexOf(':'); if (i > 0) headers[l.slice(0, i).trim()] = l.slice(i + 1).trim() })
    if (Object.keys(headers).length) srv.headers = headers
    config.mcpServers[newSrv.value.name] = srv
    raw.value = JSON.stringify(config, null, 2)
    save()
    showAdd.value = false
    newSrv.value = { name: '', url: '', headers: '' }
  } catch {}
}
</script>
