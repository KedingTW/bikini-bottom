<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">角色配置</span>
    <button @click="load()" class="ml-auto bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </div>

  <div class="p-7">
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
    </div>

    <!-- Agent List -->
    <div v-else class="space-y-3">
      <div v-for="a in agents" :key="a.name" class="glass rounded-xl overflow-hidden">
        <!-- Header -->
        <div class="px-5 py-3 flex items-center gap-3 cursor-pointer hover:bg-white/5" @click="toggleAgent(a.name)">
          <img :src="'/avatar/' + a.name" class="w-8 h-8 rounded-full object-cover border border-white/20" @error="$event.target.style.display='none'">
          <div class="flex-1 min-w-0">
            <span class="font-medium">{{ a.display }}</span>
            <span class="text-xs text-white/50 ml-2">{{ a.role }}</span>
          </div>
          <div class="flex items-center gap-3 text-xs text-white/50">
            <span title="MCP Servers">🔌 {{ a.mcp_servers }}</span>
            <span title="Skills">🧠 {{ a.skills_count }}</span>
            <span title="Steering">📋 {{ a.steering_count }}</span>
          </div>
          <span class="text-white/40 text-sm">{{ expanded === a.name ? '▾' : '▸' }}</span>
        </div>

        <!-- Expanded Detail -->
        <div v-if="expanded === a.name" class="border-t border-white/10 px-5 py-4">
          <div class="flex gap-2 mb-4">
            <button v-for="t in detailTabs" :key="t.key" @click="detailTab = t.key"
              :class="detailTab === t.key ? 'bg-cyan-600 text-white' : 'text-white/60 hover:text-white'"
              class="px-3 py-1 rounded text-xs font-medium transition">{{ t.label }}</button>
          </div>

          <!-- MCP Tab -->
          <div v-if="detailTab === 'mcp'">
            <div v-if="mcpLoading" class="py-4 text-center text-white/50 text-sm">載入中...</div>
            <div v-else>
              <textarea v-model="mcpRaw" rows="15" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-xs font-mono leading-relaxed resize-y"></textarea>
              <div class="flex items-center gap-3 mt-3">
                <button @click="saveMcp(a.name)" class="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-1.5 rounded text-xs font-medium">💾 儲存</button>
                <span v-if="mcpStatus" class="text-xs" :class="mcpStatus.ok ? 'text-green-400' : 'text-red-400'">{{ mcpStatus.text }}</span>
              </div>
            </div>
          </div>

          <!-- Skills Tab -->
          <div v-if="detailTab === 'skills'">
            <div v-if="!a.skills.length" class="text-white/50 text-sm py-4">無 Skills</div>
            <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-2">
              <div v-for="s in a.skills" :key="s" class="bg-ocean-800/50 rounded px-3 py-2 text-sm flex items-center gap-2">
                <span class="text-cyan-400">🧠</span>
                <span class="truncate">{{ s }}</span>
              </div>
            </div>
          </div>

          <!-- Steering Tab -->
          <div v-if="detailTab === 'steering'">
            <div v-if="!a.steering.length" class="text-white/50 text-sm py-4">無 Steering 檔案</div>
            <div v-else class="space-y-1.5">
              <div v-for="f in a.steering" :key="f" class="bg-ocean-800/50 rounded px-3 py-2 text-sm flex items-center gap-2 cursor-pointer hover:bg-ocean-800" @click="viewSteering(a.name, f)">
                <span class="text-cyan-400">📋</span>
                <span class="truncate">{{ f }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Steering Viewer -->
  <div v-if="steeringView" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="steeringView = null">
    <div class="bg-ocean-700 rounded-xl w-[90%] max-w-3xl max-h-[80vh] flex flex-col shadow-2xl">
      <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between font-semibold shrink-0">
        <span>📋 {{ steeringView.filename }}</span>
        <button @click="steeringView = null" class="text-2xl text-white/60 hover:text-white">&times;</button>
      </div>
      <div class="px-6 py-4 overflow-y-auto flex-1">
        <pre class="text-xs leading-relaxed whitespace-pre-wrap break-words text-white/90 bg-black/30 p-4 rounded-lg">{{ steeringView.content }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, put } = useApi()

const loading = ref(false)
const agents = ref([])
const expanded = ref(null)
const detailTab = ref('mcp')
const mcpRaw = ref('')
const mcpLoading = ref(false)
const mcpStatus = ref(null)
const steeringView = ref(null)

const detailTabs = [
  { key: 'mcp', label: '🔌 MCP' },
  { key: 'skills', label: '🧠 Skills' },
  { key: 'steering', label: '📋 Steering' },
]

async function load() {
  loading.value = true
  const res = await get('/api/agents')
  agents.value = res?.agents || []
  loading.value = false
}

async function toggleAgent(name) {
  if (expanded.value === name) { expanded.value = null; return }
  expanded.value = name
  detailTab.value = 'mcp'
  mcpStatus.value = null
  await loadMcp(name)
}

async function loadMcp(name) {
  mcpLoading.value = true
  const res = await get(`/api/agents/${name}/mcp`)
  mcpRaw.value = res?.raw || '{}'
  mcpLoading.value = false
}

async function saveMcp(name) {
  mcpStatus.value = null
  try {
    const res = await put(`/api/agents/${name}/mcp`, { raw: mcpRaw.value })
    if (res?.ok) mcpStatus.value = { ok: true, text: '✅ 已儲存' }
    else mcpStatus.value = { ok: false, text: '❌ ' + (res?.detail || '儲存失敗') }
  } catch (e) { mcpStatus.value = { ok: false, text: '❌ ' + e.message } }
}

async function viewSteering(agent, filename) {
  const res = await get(`/api/agents/${agent}/steering/${filename}`)
  if (res?.content) steeringView.value = { filename, content: res.content }
}

onMounted(load)
</script>
