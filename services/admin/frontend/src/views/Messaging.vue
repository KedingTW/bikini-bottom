<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">訊息推送</span>
  </div>

  <div class="p-7">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Form -->
      <div class="glass rounded-xl p-6">
        <h3 class="font-semibold mb-5 text-cyan-300">💬 發送訊息</h3>

        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">平台</label>
          <select v-model="platform" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-2.5 text-sm">
            <option value="discord">Discord</option>
            <option value="wecom" disabled>企業微信（即將推出）</option>
          </select>
        </div>

        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">目標頻道</label>
          <select v-model="channel" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-2.5 text-sm">
            <option value="">選擇頻道...</option>
            <option v-for="c in filteredChannels" :key="c.id" :value="c.id">#{{ c.name }}</option>
          </select>
        </div>

        <div class="mb-5">
          <label class="block text-sm text-white/70 mb-1.5">訊息內容</label>
          <textarea v-model="content" rows="8" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-sm resize-y leading-relaxed" placeholder="輸入要發送的訊息..."></textarea>
          <div class="text-xs text-white/40 mt-1.5">支援 Discord Markdown 語法（**粗體**、*斜體*、`程式碼`）</div>
        </div>

        <div class="flex items-center gap-4">
          <button @click="send" :disabled="!channel || !content.trim() || sending"
            class="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-lg text-sm font-medium transition">
            {{ sending ? '發送中...' : '發送' }}
          </button>
          <span v-if="status" class="text-sm" :class="status.ok ? 'text-green-400' : 'text-red-400'">{{ status.text }}</span>
        </div>
      </div>

      <!-- Preview -->
      <div class="glass rounded-xl p-6">
        <h3 class="font-semibold mb-5 text-white/50">📋 預覽</h3>
        <div v-if="!content.trim()" class="text-center py-12 text-white/30">輸入內容後顯示預覽</div>
        <div v-else class="bg-ocean-800/50 rounded-lg p-4">
          <div class="flex items-center gap-2 mb-2">
            <img src="https://cdn.discordapp.com/avatars/1508396648596770826/74a960980e938d0513fe034c7352dff1.png?size=32" class="w-8 h-8 rounded-full">
            <div>
              <span class="font-medium text-sm">凱倫</span>
              <span class="text-xs text-white/40 ml-2">今天</span>
            </div>
          </div>
          <div class="text-sm text-white/90 whitespace-pre-wrap pl-10">{{ content }}</div>
        </div>
        <div v-if="channel" class="mt-3 text-xs text-white/40">將發送到 #{{ getChannelName(channel) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'
const { get } = useApi()

const EXCLUDED_IDS = new Set(['1492090122257170526', '1503703338800382002', '1508387929364631562'])

const platform = ref('discord')
const channels = ref([])
const channel = ref('')
const content = ref('')
const status = ref(null)
const sending = ref(false)

const filteredChannels = computed(() => channels.value.filter(c => !EXCLUDED_IDS.has(c.id)))

function getChannelName(id) {
  const c = channels.value.find(c => c.id === id)
  return c ? c.name : ''
}

async function send() {
  status.value = null
  sending.value = true
  try {
    const res = await fetch(`/api/discord/channels/${channel.value}/messages`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content.value })
    })
    const data = await res.json()
    if (res.ok) { status.value = { ok: true, text: '✅ 已發送' }; content.value = '' }
    else status.value = { ok: false, text: '❌ ' + (data.detail || '失敗') }
  } catch { status.value = { ok: false, text: '❌ 網路錯誤' } }
  sending.value = false
}

onMounted(async () => {
  const res = await get('/api/discord/channels')
  channels.value = res?.channels || []
})
</script>
