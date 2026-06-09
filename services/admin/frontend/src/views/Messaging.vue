<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <span class="font-medium">訊息推送</span>
    <div class="flex gap-1 ml-4">
      <button v-for="t in tabs" :key="t.key" @click="tab = t.key"
        :class="tab === t.key ? 'bg-cyan-600 text-white' : 'text-white/60 hover:text-white'"
        class="px-3 py-1 rounded text-xs font-medium transition">{{ t.label }}</button>
    </div>
  </div>

  <div class="p-7">
    <!-- Discord Tab -->
    <div v-if="tab === 'discord'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="glass rounded-xl p-6">
        <h3 class="font-semibold mb-4 text-cyan-300">💬 Discord 推送</h3>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">目標頻道</label>
          <select v-model="discord.channel" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-2.5 text-sm">
            <option value="">選擇頻道...</option>
            <option v-for="c in filteredChannels" :key="c.id" :value="c.id">#{{ c.name }}</option>
          </select>
        </div>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">訊息內容</label>
          <textarea v-model="discord.content" rows="6" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-sm resize-y" placeholder="支援 Markdown"></textarea>
        </div>
        <div class="flex items-center gap-3">
          <button @click="sendDiscord()" :disabled="!discord.channel || !discord.content.trim() || sending"
            class="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white px-5 py-2 rounded-lg text-sm font-medium">{{ sending ? '發送中...' : '🚀 發送' }}</button>
          <span v-if="discord.status" class="text-sm" :class="discord.status.ok ? 'text-green-400' : 'text-red-400'">{{ discord.status.text }}</span>
        </div>
      </div>
      <div class="glass rounded-xl p-6">
        <h3 class="font-semibold mb-4 text-white/50">📋 預覽</h3>
        <div v-if="discord.content.trim()" class="bg-ocean-800/50 rounded-lg p-4 text-sm text-white/90 whitespace-pre-wrap">{{ discord.content }}</div>
        <div v-else class="text-center py-8 text-white/30">輸入內容後顯示預覽</div>
      </div>
    </div>

    <!-- WeCom Tab -->
    <div v-if="tab === 'wecom'" class="max-w-2xl">
      <div class="glass rounded-xl p-6">
        <h3 class="font-semibold mb-4 text-cyan-300">🏢 企業微信推送</h3>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">Webhook URL</label>
          <input v-model="wecom.webhook" type="url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
            class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-2.5 text-sm font-mono">
          <div class="text-xs text-white/40 mt-1">群機器人的 Webhook 地址</div>
        </div>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">訊息內容</label>
          <textarea v-model="wecom.content" rows="6" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-sm resize-y" placeholder="純文字訊息"></textarea>
        </div>
        <div class="flex items-center gap-3">
          <button @click="sendWecom()" :disabled="!wecom.webhook || !wecom.content.trim() || sending"
            class="bg-green-600 hover:bg-green-500 disabled:opacity-40 text-white px-5 py-2 rounded-lg text-sm font-medium">{{ sending ? '推送中...' : '🚀 推送' }}</button>
          <span v-if="wecom.status" class="text-sm" :class="wecom.status.ok ? 'text-green-400' : 'text-red-400'">{{ wecom.status.text }}</span>
        </div>
      </div>
    </div>

    <!-- Schedule Tab -->
    <div v-if="tab === 'schedule'" class="max-w-2xl">
      <div class="glass rounded-xl p-6">
        <h3 class="font-semibold mb-4 text-cyan-300">⏰ 排程推送</h3>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">平台</label>
          <select v-model="schedule.platform" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-2.5 text-sm">
            <option value="discord">Discord</option>
            <option value="wecom">企業微信</option>
          </select>
        </div>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">目標</label>
          <input v-model="schedule.target" placeholder="頻道 ID 或 Webhook URL"
            class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-2.5 text-sm">
        </div>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">排程時間</label>
          <input v-model="schedule.scheduledAt" type="datetime-local"
            class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-2.5 text-sm">
        </div>
        <div class="mb-4">
          <label class="block text-sm text-white/70 mb-1.5">訊息內容</label>
          <textarea v-model="schedule.content" rows="5" class="w-full bg-ocean-800 text-white border border-white/20 rounded-lg px-4 py-3 text-sm resize-y" placeholder="排程發送的內容"></textarea>
        </div>
        <div class="flex items-center gap-3">
          <button @click="submitSchedule()" :disabled="!schedule.content.trim() || !schedule.scheduledAt || sending"
            class="bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-white px-5 py-2 rounded-lg text-sm font-medium">{{ sending ? '提交中...' : '⏰ 建立排程' }}</button>
          <span v-if="schedule.status" class="text-sm" :class="schedule.status.ok ? 'text-green-400' : 'text-red-400'">{{ schedule.status.text }}</span>
        </div>
      </div>
    </div>

    <!-- History Tab -->
    <div v-if="tab === 'history'">
      <div class="glass rounded-xl p-5">
        <div class="flex items-center gap-3 mb-4">
          <h3 class="font-semibold text-cyan-300">📋 推送歷史</h3>
          <button @click="loadHistory()" class="text-xs px-3 py-1 rounded border border-white/20 text-white/70 hover:bg-white/10">🔄 更新</button>
        </div>
        <div v-if="!history.length" class="text-white/50 text-sm py-4">尚無推送紀錄</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead><tr class="bg-ocean-800/60">
              <th class="text-left px-4 py-2 font-semibold">時間</th>
              <th class="text-left px-4 py-2 font-semibold">操作者</th>
              <th class="text-left px-4 py-2 font-semibold">平台</th>
              <th class="text-left px-4 py-2 font-semibold">狀態</th>
              <th class="text-left px-4 py-2 font-semibold">內容</th>
            </tr></thead>
            <tbody>
              <tr v-for="h in history" :key="h.ts" class="border-t border-white/5">
                <td class="px-4 py-2 text-white/60 text-xs font-mono whitespace-nowrap">{{ h.ts }}</td>
                <td class="px-4 py-2">{{ h.user }}</td>
                <td class="px-4 py-2"><span :class="h.platform === 'discord' ? 'text-cyan-300' : 'text-green-300'">{{ h.platform }}</span></td>
                <td class="px-4 py-2">
                  <span :class="h.status === 'sent' ? 'text-green-400' : 'text-amber-400'">{{ h.status === 'sent' ? '✅ 已發送' : '⏰ 已排程' }}</span>
                  <span v-if="h.scheduled_at" class="text-xs text-white/40 ml-1">{{ h.scheduled_at }}</span>
                </td>
                <td class="px-4 py-2 text-white/70 text-xs max-w-[200px] truncate">{{ h.content }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'
const { get, post } = useApi()

const EXCLUDED_IDS = new Set(['1492090122257170526', '1503703338800382002', '1508387929364631562'])
const tabs = [
  { key: 'discord', label: '💬 Discord' },
  { key: 'wecom', label: '🏢 企業微信' },
  { key: 'schedule', label: '⏰ 排程' },
  { key: 'history', label: '📋 歷史' },
]
const tab = ref('discord')
const channels = ref([])
const sending = ref(false)
const history = ref([])

const discord = reactive({ channel: '', content: '', status: null })
const wecom = reactive({ webhook: '', content: '', status: null })
const schedule = reactive({ platform: 'discord', target: '', content: '', scheduledAt: '', status: null })

const filteredChannels = computed(() => channels.value.filter(c => !EXCLUDED_IDS.has(c.id)))

async function sendDiscord() {
  discord.status = null
  sending.value = true
  try {
    const res = await fetch(`/api/discord/channels/${discord.channel}/messages`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: discord.content })
    })
    const data = await res.json()
    if (res.ok) { discord.status = { ok: true, text: '✅ 已發送' }; discord.content = '' }
    else discord.status = { ok: false, text: '❌ ' + (data.detail || '失敗') }
  } catch { discord.status = { ok: false, text: '❌ 網路錯誤' } }
  sending.value = false
}

async function sendWecom() {
  wecom.status = null
  sending.value = true
  const res = await post('/api/messaging/wecom', { content: wecom.content, webhook_url: wecom.webhook })
  if (res?.ok) { wecom.status = { ok: true, text: '✅ 已推送' }; wecom.content = '' }
  else wecom.status = { ok: false, text: '❌ ' + (res?.detail || '推送失敗') }
  sending.value = false
}

async function submitSchedule() {
  schedule.status = null
  sending.value = true
  const res = await post('/api/messaging/schedule', {
    platform: schedule.platform, target: schedule.target,
    content: schedule.content, scheduled_at: schedule.scheduledAt
  })
  if (res?.ok) { schedule.status = { ok: true, text: res.message || '✅ 已排程' }; schedule.content = '' }
  else schedule.status = { ok: false, text: '❌ ' + (res?.detail || '排程失敗') }
  sending.value = false
}

async function loadHistory() {
  const res = await get('/api/messaging/history')
  if (res) history.value = res.history || []
}

onMounted(async () => {
  const [chRes] = await Promise.all([get('/api/discord/channels'), loadHistory()])
  channels.value = chRes?.channels || []
})
</script>
