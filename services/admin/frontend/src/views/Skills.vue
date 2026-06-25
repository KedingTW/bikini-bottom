<template>
  <div class="p-4 sm:p-6">
    <div class="flex items-center gap-3 mb-5">
      <h2 class="text-lg font-semibold">技能管理</h2>
      <span class="text-xs text-white/50">{{ skills.length }} 個技能</span>
    </div>

    <div v-if="loading" class="text-center py-10 text-white/50">載入中...</div>
    <div v-else-if="!skills.length" class="text-center py-20 text-white/50">
      <div class="text-3xl mb-2">📚</div>
      <div>尚未有任何技能</div>
    </div>
    <div v-else class="space-y-3">
      <div v-for="s in skills" :key="s.name" class="bg-ocean-800/50 rounded-lg border border-white/5 p-4 cursor-pointer hover:border-cyan-400/20 transition" @click="openAssign(s)">
        <div class="flex items-center gap-3">
          <span class="text-lg">📚</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-medium text-sm text-cyan-300">{{ s.display_name || s.name }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded" :class="s.source === 'local' ? 'bg-green-600/20 text-green-300' : 'bg-blue-600/20 text-blue-300'">{{ s.source === 'local' ? '🏠 本地' : '🔗 外部' }}</span>
            </div>
            <div class="text-[11px] text-white/50 truncate mt-0.5">{{ s.description || '無描述' }}</div>
          </div>
          <span class="text-xs text-white/40">{{ s.enabled_agents?.length || 0 }} 角色啟用</span>
          <span class="text-white/30">›</span>
        </div>
      </div>
    </div>

    <!-- Agent Assignment Dialog -->
    <div v-if="assignDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="assignDialog = null">
      <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
        <h3 class="text-lg font-semibold mb-1">{{ assignDialog.display_name || assignDialog.name }}</h3>
        <p class="text-xs text-white/40 mb-4">選擇要啟用此技能的角色</p>

        <div v-if="agentsLoading" class="text-center py-4 text-white/50 text-sm">載入角色...</div>
        <div v-else class="space-y-1 max-h-[300px] overflow-y-auto">
          <label v-for="a in allAgents" :key="a.name" class="flex items-center gap-3 px-3 py-2.5 rounded hover:bg-white/5 cursor-pointer">
            <input type="checkbox" :value="a.name" v-model="assignDialog.selectedAgents" class="w-4 h-4 accent-cyan-500">
            <img v-if="a.avatar_url" :src="a.avatar_url" class="w-6 h-6 rounded-full object-cover">
            <span class="text-sm text-white/90">{{ a.display }}</span>
          </label>
        </div>

        <div v-if="assignError" class="mt-3 text-sm text-red-400">{{ assignError }}</div>
        <div class="flex gap-3 justify-end mt-4">
          <button @click="assignDialog = null" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
          <button @click="saveAssign()" :disabled="assignSaving" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium disabled:opacity-50">💾 儲存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, put } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const skills = ref([])
const loading = ref(false)
const allAgents = ref([])
const agentsLoading = ref(false)
const assignDialog = ref(null)
const assignError = ref('')
const assignSaving = ref(false)

async function load() {
  loading.value = true
  const res = await get('/api/skills')
  skills.value = res?.skills || []
  loading.value = false
}

async function loadAgents() {
  agentsLoading.value = true
  const res = await get(`/api/agents?group=${currentGroup.value}`)
  allAgents.value = res?.agents || []
  agentsLoading.value = false
}

function openAssign(s) {
  assignError.value = ''
  assignDialog.value = {
    name: s.name,
    display_name: s.display_name,
    selectedAgents: [...(s.enabled_agents || [])]
  }
  if (!allAgents.value.length) loadAgents()
}

async function saveAssign() {
  assignSaving.value = true
  assignError.value = ''
  const res = await put(`/api/skills/${assignDialog.value.name}/agents`, {
    enabled_agents: assignDialog.value.selectedAgents
  })
  if (res?.ok) { assignDialog.value = null; load() }
  else { assignError.value = res?.detail || '儲存失敗' }
  assignSaving.value = false
}

onMounted(load)
</script>
