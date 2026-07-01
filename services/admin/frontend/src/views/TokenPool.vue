<template>
  <div class="p-4 sm:p-6">
    <div class="flex items-center gap-3 mb-5 flex-wrap">
      <h2 class="text-lg font-semibold">Bot Token 池</h2>
      <span class="text-xs text-white/50">可用 {{ available }} / 總共 {{ tokens.length }}</span>
      <button @click="openAdd()" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">+ 新增 Token</button>
    </div>

    <div v-if="loading" class="text-center py-10 text-white/50">載入中...</div>
    <div v-else-if="!tokens.length" class="text-center py-20 text-white/50">
      <div class="text-3xl mb-2">🔑</div>
      <div>尚未新增任何 Bot Token</div>
    </div>
    <div v-else class="space-y-2">
      <div v-for="t in tokens" :key="t.id" class="bg-ocean-800/50 rounded-lg border border-white/5 p-4 flex items-center gap-4">
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-white/90">{{ t.bot_name || '未命名' }}</div>
          <div class="text-xs text-white/40 font-mono">{{ t.bot_id.slice(0, 6) }}...{{ t.bot_id.slice(-4) }}</div>
        </div>
        <span class="text-[10px] px-2 py-0.5 rounded" :class="{
          'bg-green-600/20 text-green-300': t.status === 'available',
          'bg-blue-600/20 text-blue-300': t.status === 'in-use',
          'bg-white/10 text-white/40': t.status === 'disabled'
        }">{{ t.status === 'available' ? '可用' : t.status === 'in-use' ? '使用中' : '停用' }}</span>
        <span v-if="t.assigned_to" class="text-xs text-white/40">→ {{ t.assigned_to }}</span>
        <span class="text-[10px] text-white/20">{{ t.created_at?.slice(0, 10) }}</span>
        <button @click="toggleStatus(t)" :disabled="t.status === 'in-use'" class="text-xs px-2 py-1 rounded border border-white/15 hover:bg-white/10 disabled:opacity-30">{{ t.status === 'disabled' ? '啟用' : '停用' }}</button>
        <button @click="deleteToken(t)" :disabled="t.status !== 'available'" class="text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10 disabled:opacity-30">🗑️</button>
      </div>
    </div>

    <!-- Add Dialog -->
    <div v-if="addDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="addDialog = false">
      <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
        <h3 class="text-lg font-semibold mb-4">新增 Bot Token</h3>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">名稱</label>
          <input v-model="addForm.name" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none focus:border-cyan-400/60" placeholder="如：臨時工 A">
        </div>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">Token <span class="text-red-400">*</span></label>
          <textarea v-model="addForm.token" rows="3" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-xs font-mono focus:outline-none focus:border-cyan-400/60" placeholder="貼上 Discord Bot Token"></textarea>
        </div>
        <div v-if="addError" class="mb-3 text-sm text-red-400">{{ addError }}</div>
        <div class="flex gap-3 justify-end">
          <button @click="addDialog = false" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70">取消</button>
          <button @click="doAdd()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">新增</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, post } = useApi()
const tokens = ref([])
const loading = ref(false)
const addDialog = ref(false)
const addForm = ref({ name: '', token: '' })
const addError = ref('')

const available = computed(() => tokens.value.filter(t => t.status === 'available').length)

async function load() {
  loading.value = true
  const res = await get('/api/token-pool')
  tokens.value = res?.tokens || []
  loading.value = false
}

function openAdd() { addDialog.value = true; addForm.value = { name: '', token: '' }; addError.value = '' }

async function doAdd() {
  addError.value = ''
  if (!addForm.value.token.trim()) { addError.value = 'Token 為必填'; return }
  const res = await post('/api/token-pool', { token: addForm.value.token.trim(), bot_name: addForm.value.name.trim() })
  if (res?.ok) { addDialog.value = false; load() }
  else { addError.value = res?.detail || '新增失敗' }
}

async function toggleStatus(t) {
  const newStatus = t.status === 'disabled' ? 'available' : 'disabled'
  await fetch(`/api/token-pool/${t.id}/status`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: newStatus }) })
  load()
}

async function deleteToken(t) {
  if (!confirm(`確定刪除 ${t.bot_name || t.bot_id}？`)) return
  await fetch(`/api/token-pool/${t.id}`, { method: 'DELETE' })
  load()
}

onMounted(load)
</script>
