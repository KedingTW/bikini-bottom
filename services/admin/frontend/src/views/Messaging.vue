<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">訊息推送</span>
  </div>

  <div class="p-7">
    <div class="glass rounded-xl p-6 max-w-2xl">
      <h3 class="font-semibold mb-4 text-cyan-300">📢 發送公告</h3>
      <div class="mb-4">
        <label class="block text-sm text-white/70 mb-1">平台</label>
        <select v-model="platform" class="w-full bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm">
          <option value="discord">Discord</option>
          <option value="wecom" disabled>企業微信（即將推出）</option>
        </select>
      </div>
      <div class="mb-4">
        <label class="block text-sm text-white/70 mb-1">目標頻道</label>
        <select v-model="channel" class="w-full bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm">
          <option value="">選擇頻道...</option>
          <option v-for="c in channels" :key="c.id" :value="c.id">#{{ c.name }}</option>
        </select>
      </div>
      <div class="mb-4">
        <label class="block text-sm text-white/70 mb-1">訊息內容</label>
        <textarea v-model="content" rows="5" class="w-full bg-ocean-800 text-white border border-white/20 rounded px-3 py-2 text-sm resize-y" placeholder="輸入訊息..."></textarea>
      </div>
      <div class="flex items-center gap-3">
        <button @click="send" :disabled="!channel || !content.trim()" class="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-5 py-2 rounded text-sm font-medium transition">發送</button>
        <span v-if="status" class="text-sm" :class="status.ok ? 'text-green-400' : 'text-red-400'">{{ status.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'
const { get } = useApi()

const platform = ref('discord')
const channels = ref([])
const channel = ref('')
const content = ref('')
const status = ref(null)

async function send() {
  status.value = null
  try {
    const res = await fetch(`/api/discord/channels/${channel.value}/messages`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content.value })
    })
    const data = await res.json()
    if (res.ok) { status.value = { ok: true, text: '✅ 已發送' }; content.value = '' }
    else status.value = { ok: false, text: '❌ ' + (data.detail || '失敗') }
  } catch { status.value = { ok: false, text: '❌ 網路錯誤' } }
}

onMounted(async () => {
  const res = await get('/api/discord/channels')
  channels.value = res?.channels || []
})
</script>
