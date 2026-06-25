<template>
  <div class="p-4 sm:p-6">
    <div class="flex items-center gap-3 mb-5 flex-wrap">
      <h2 class="text-lg font-semibold">技能管理</h2>
      <span class="text-xs text-white/50">{{ skills.length }} 個技能</span>
      <button @click="openAdd()" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white">+ 新增技能</button>
    </div>

    <div v-if="loading" class="text-center py-10 text-white/50">載入中...</div>
    <div v-else-if="!skills.length" class="text-center py-20 text-white/50">
      <div class="text-3xl mb-2">📚</div>
      <div>尚未建立任何技能</div>
    </div>
    <div v-else class="space-y-3">
      <div v-for="s in skills" :key="s.name" class="bg-ocean-800/50 rounded-lg border border-white/5 p-4">
        <div class="flex items-center gap-3">
          <span class="text-lg">📚</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-medium text-sm text-cyan-300">{{ s.display_name || s.name }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded" :class="s.source === 'local' ? 'bg-green-600/20 text-green-300' : 'bg-blue-600/20 text-blue-300'">{{ s.source === 'local' ? '🏠 本地' : '🔗 外部' }}</span>
            </div>
            <div class="text-[11px] text-white/50 truncate mt-0.5">{{ s.description || '無描述' }}</div>
          </div>
          <span v-if="s.used_by_count" class="text-[10px] px-2 py-0.5 rounded bg-ocean-700 text-white/60">{{ s.used_by_count }} 角色使用中</span>
          <button @click="openEdit(s)" :disabled="s.source !== 'local'" class="text-xs px-2 py-1 rounded border border-white/15 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed">✏️ 編輯</button>
          <button @click="confirmDelete(s)" :disabled="s.source !== 'local'" class="text-xs px-2 py-1 rounded border border-red-400/30 text-red-300 hover:bg-red-400/10 disabled:opacity-30 disabled:cursor-not-allowed">🗑️ 刪除</button>
        </div>
      </div>
    </div>

    <!-- Add/Edit Dialog -->
    <div v-if="dialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="dialog = null">
      <div class="bg-ocean-700 rounded-xl w-full max-w-2xl p-6 shadow-2xl border border-white/10 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">{{ dialog.mode === 'add' ? '新增' : '編輯' }}技能</h3>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">Skill ID <span v-if="dialog.mode === 'add'" class="text-red-400">*</span></label>
          <input v-model="dialog.name" :disabled="dialog.mode === 'edit'" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm font-mono focus:outline-none focus:border-cyan-400/60 disabled:opacity-50" placeholder="e.g. my-skill">
        </div>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">中文顯示名</label>
          <input v-model="dialog.display_name" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-sm focus:outline-none focus:border-cyan-400/60" placeholder="e.g. 我的技能">
        </div>
        <div class="mb-3">
          <label class="block text-sm text-white/70 mb-1">SKILL.md 內容</label>
          <textarea v-model="dialog.content" rows="15" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white text-xs font-mono leading-relaxed focus:outline-none focus:border-cyan-400/60 resize-y"></textarea>
        </div>
        <div v-if="dialog.error" class="mb-3 text-sm text-red-400">{{ dialog.error }}</div>
        <div class="flex gap-3 justify-end">
          <button @click="dialog = null" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
          <button @click="saveDialog()" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">💾 {{ dialog.mode === 'add' ? '新增' : '儲存' }}</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="deleteTarget = null">
      <div class="bg-ocean-700 rounded-xl w-full max-w-sm p-6 shadow-2xl border border-white/10 text-center">
        <h3 class="text-lg font-semibold mb-2">確定刪除？</h3>
        <p class="text-sm text-white/60 mb-4">將刪除技能「{{ deleteTarget.display_name || deleteTarget.name }}」，此操作不可復原。</p>
        <div class="flex gap-3 justify-center">
          <button @click="deleteTarget = null" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
          <button @click="doDelete()" class="px-4 py-2 text-sm rounded-lg bg-red-600 hover:bg-red-500 text-white font-medium">🗑️ 刪除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, post, put } = useApi()
const skills = ref([])
const loading = ref(false)
const dialog = ref(null)
const deleteTarget = ref(null)

async function load() {
  loading.value = true
  const res = await get('/api/skills')
  skills.value = res?.skills || []
  loading.value = false
}

function openAdd() {
  dialog.value = { mode: 'add', name: '', display_name: '', content: '', error: '' }
}

async function openEdit(s) {
  const res = await get(`/api/skills/${s.name}`)
  dialog.value = {
    mode: 'edit', name: s.name,
    display_name: res?.display_name || s.display_name || '',
    content: res?.content || '',
    error: ''
  }
}

async function saveDialog() {
  const d = dialog.value
  if (!d.name.trim()) { d.error = 'Skill ID 為必填'; return }
  const body = { name: d.name.trim(), display_name: d.display_name.trim(), content: d.content }
  let res
  if (d.mode === 'add') res = await post('/api/skills', body)
  else res = await put(`/api/skills/${d.name}`, body)
  if (res?.ok) { dialog.value = null; load() }
  else { d.error = res?.detail || '操作失敗' }
}

function confirmDelete(s) { deleteTarget.value = s }

async function doDelete() {
  const res = await fetch(`/api/skills/${deleteTarget.value.name}`, { method: 'DELETE' })
  deleteTarget.value = null
  if (res.ok) load()
}

onMounted(load)
</script>
