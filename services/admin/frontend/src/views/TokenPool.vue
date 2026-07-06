<template>
  <div class="p-4 sm:p-6">
    <div class="flex items-center gap-3 mb-5 flex-wrap">
      <h2 class="text-lg font-semibold">帳號池</h2>
      <span class="text-xs text-white/50">可用 {{ available }} / 總共 {{ tokens.length }}</span>
      <button @click="openAdd()" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">+ 新增帳號</button>
    </div>

    <div v-if="loading" class="text-center py-10 text-white/50">載入中...</div>
    <div v-else-if="!tokens.length" class="text-center py-20 text-white/50">
      <div class="text-3xl mb-2">🔑</div>
      <div>尚未新增任何帳號</div>
    </div>
    <div v-else class="space-y-2">
      <div v-for="(t, i) in tokens" :key="t.id" class="bg-ocean-800/50 rounded-lg border border-white/5 p-4 flex items-center gap-4">
        <span class="text-sm text-white/50 font-mono w-8">#{{ i + 1 }}</span>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-white/90 font-mono">Bot ID: ...{{ t.bot_id.slice(-4) }}</div>
        </div>
        <span class="text-[10px] px-2 py-0.5 rounded" :class="{
          'bg-green-600/20 text-green-300': t.status === 'available',
          'bg-blue-600/20 text-blue-300': t.status === 'in-use',
          'bg-white/10 text-white/40': t.status === 'disabled'
        }">{{ t.status === 'available' ? '可用' : t.status === 'in-use' ? '使用中' : '停用' }}</span>
        <span v-if="t.assigned_to" class="text-xs text-white/40">→ {{ t.assigned_to }}</span>
        <span class="text-[10px] text-white/20">{{ t.created_at?.slice(0, 10) }}</span>
        <button @click="openUpdate(t)" class="text-xs px-2 py-1 rounded border border-white/15 hover:bg-white/10">ð æ´æ°</button>
        <button @click="toggleStatus(t)" :disabled="t.status === 'in-use'" class="text-xs px-2 py-1 rounded border border-white/15 hover:bg-white/10 disabled:opacity-30">{{ t.status === 'disabled' ? '啟用' : '停用' }}</button>
        <button @click="deleteToken(t)" :disabled="t.status !== 'disabled'" class="text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10 disabled:opacity-30">🗑️</button>
      </div>
    </div>

    <!-- Update Token Dialog -->
    <div v-if="updateDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="updateDialog = null">
      <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
        <h3 class="text-lg font-semibold mb-4">æ´æ° Token â #{{ updateDialog.index }}</h3>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">è²¼ä¸æ°ç Bot Token</label>
          <textarea v-model="updateDialog.token" rows="3" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-xs font-mono focus:outline-none focus:border-cyan-400/60"></textarea>
        </div>
        <div v-if="updateDialog.error" class="mb-3 text-sm text-red-400">{{ updateDialog.error }}</div>
        <div class="flex gap-3 justify-end">
          <button @click="updateDialog = null" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70">åæ¶</button>
          <button @click="doUpdate()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">è¦è</button>
        </div>
      </div>
    </div>

    <!-- Add Dialog -->
    <div v-if="addDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="addDialog = false">
      <div class="bg-ocean-700 rounded-xl w-full max-w-2xl p-6 shadow-2xl border border-white/10">
        <h3 class="text-lg font-semibold mb-3">新增帳號</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
          <!-- 左：Token 輸入 -->
          <div>
            <div class="mb-3">
              <label class="block text-sm text-white/70 mb-1">貼上 Bot Token <span class="text-red-400">*</span></label>
          <textarea v-model="addForm.token" rows="5" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-xs font-mono focus:outline-none focus:border-cyan-400/60 min-h-[120px]" placeholder="貼上 Discord Bot Token"></textarea>
        </div>
            <div v-if="addError" class="text-sm text-red-400 mt-2">{{ addError }}</div>
          </div>
          <!-- 右：說明 -->
          <div class="text-xs text-white/50 space-y-0.5 max-h-[250px] overflow-y-auto">
            <a href="https://discord.com/developers/applications" target="_blank" class="inline-block mb-2 text-sm text-cyan-400 hover:underline">↗ 前往 Discord Developer Portal 建立新應用</a>
            <div class="font-medium text-white/70 mb-1">設置步驟：</div>
            <div>2. 進入「機器人」頁面：</div>
            <div class="pl-3">- 點「重設權杖」取得 Token</div>
            <div class="pl-3">- 開啟以下 Privileged Gateway Intents（全部打開）：</div>
            <div class="pl-5">✓ Presence Intent</div>
            <div class="pl-5">✓ Server Members Intent</div>
            <div class="pl-5">✓ Message Content Intent</div>
            <div class="mt-1">3. 進入「OAuth2」頁面 → OAuth2 URL 產生器：</div>
            <div class="pl-3">- 範圍：勾選「bot」</div>
            <div class="pl-3">- 一般權限：勾選「檢視頻道」</div>
            <div class="pl-3">- 文字權限：勾選以下項目：</div>
            <div class="pl-5">✓ 傳送訊息</div>
            <div class="pl-5">✓ 建立公開討論串</div>
            <div class="pl-5">✓ 在討論串中傳送訊息</div>
            <div class="pl-5">✓ 嵌入連結</div>
            <div class="pl-5">✓ 附加檔案</div>
            <div class="pl-5">✓ 讀取訊息歷史記錄</div>
            <div class="pl-5">✓ 新增反應</div>
            <div class="pl-5">✓ 使用斜線指令</div>
            <div class="mt-1">4. 複製產生的 URL，在瀏覽器開啟邀請機器人加入伺服器</div>
            <div>5. 將 Token 貼到左方欄位</div>
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-4">
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
const addForm = ref({ token: '' })
const addError = ref('')
const updateDialog = ref(null)

const available = computed(() => tokens.value.filter(t => t.status === 'available').length)

async function load() {
  loading.value = true
  const res = await get('/api/token-pool')
  tokens.value = res?.tokens || []
  loading.value = false
}

function openAdd() { addDialog.value = true; addForm.value = { token: '' }; addError.value = '' }

async function doAdd() {
  addError.value = ''
  if (!addForm.value.token.trim()) { addError.value = 'Token 為必填'; return }
  const res = await post('/api/token-pool', { token: addForm.value.token.trim() })
  if (res?.ok) { addDialog.value = false; load() }
  else { addError.value = res?.detail || '新增失敗' }
}

function openUpdate(t) {
  updateDialog.value = { id: t.id, index: tokens.value.indexOf(t) + 1, token: '', error: '' }
}

async function doUpdate() {
  if (!updateDialog.value.token.trim()) { updateDialog.value.error = 'Token çºå¿å¡«'; return }
  const res = await fetch('/api/token-pool/' + updateDialog.value.id + '/token', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: updateDialog.value.token.trim() })
  })
  const data = await res.json()
  if (res.ok) { updateDialog.value = null; load() }
  else { updateDialog.value.error = data?.detail || 'æ´æ°å¤±æ' }
}

async function toggleStatus(t) {
  const newStatus = t.status === 'disabled' ? 'available' : 'disabled'
  await fetch(`/api/token-pool/${t.id}/status`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: newStatus }) })
  load()
}

async function deleteToken(t) {
  if (!confirm(`確定刪除帳號 #${tokens.value.indexOf(t) + 1}？`)) return
  await fetch(`/api/token-pool/${t.id}`, { method: 'DELETE' })
  load()
}

onMounted(load)
</script>
