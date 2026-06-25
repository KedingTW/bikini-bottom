<template>
  <div class="flex h-full">
    <!-- Left: Skill list -->
    <div class="w-full md:w-64 shrink-0 md:border-r border-white/10 overflow-y-auto">
      <div class="p-3 border-b border-white/10">
        <h3 class="text-xs font-medium text-white/50 uppercase tracking-wider">技能 · {{ skills.length }}</h3>
      </div>
      <div v-if="loading" class="p-4 text-center text-white/50 text-sm">載入中...</div>
      <div v-else class="py-1">
        <button v-for="s in skills" :key="s.name" @click="selectSkill(s)"
          class="w-full flex items-center gap-2.5 px-3 py-2.5 text-left transition"
          :class="selected?.name === s.name ? 'bg-cyan-500/15 border-l-2 border-cyan-400' : 'hover:bg-white/5 border-l-2 border-transparent'">
          <span class="text-lg">📚</span>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium truncate" :class="selected?.name === s.name ? 'text-cyan-300' : 'text-white/90'">{{ s.display_name || s.name }}</div>
            <div class="text-[10px] text-white/50 truncate">{{ s.enabled_agents?.length || 0 }} 角色啟用</div>
          </div>
        </button>
      </div>
    </div>

    <!-- Right: Agent assignment -->
    <div class="flex-1 overflow-y-auto p-4 sm:p-6" :class="selected ? '' : 'hidden md:block'">
      <!-- Mobile back -->
      <button v-if="selected" @click="selected = null" class="md:hidden flex items-center gap-1 text-sm text-white/60 mb-4 active:text-white/80">
        <span>←</span> <span>返回技能列表</span>
      </button>

      <div v-if="!selected" class="text-center py-20 text-white/50 hidden md:block">
        <div class="text-3xl mb-2">📚</div>
        <div>點選左側技能，管理角色分配</div>
      </div>

      <div v-if="selected">
        <div class="flex items-center gap-3 mb-5">
          <h2 class="text-lg font-semibold">{{ selected.display_name || selected.name }}</h2>
          <span class="text-[10px] px-1.5 py-0.5 rounded" :class="selected.source === 'local' ? 'bg-green-600/20 text-green-300' : 'bg-blue-600/20 text-blue-300'">{{ selected.source === 'local' ? '🏠 本地' : '🔗 外部' }}</span>
          <button @click="saveAssign()" :disabled="!dirty || saving" class="ml-auto px-4 py-1.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-30 disabled:cursor-not-allowed">💾 儲存</button>
        </div>

        <p v-if="selected.description" class="text-sm text-white/50 mb-4">{{ selected.description }}</p>

        <div class="text-sm text-white/60 mb-3">選擇要啟用此技能的角色：</div>

        <div v-if="agentsLoading" class="text-sm text-white/40 py-4">載入角色中...</div>
        <div v-else class="space-y-1">
          <label v-for="a in allAgents" :key="a.name" class="flex items-center gap-3 px-3 py-2.5 rounded hover:bg-white/5 cursor-pointer">
            <input type="checkbox" :value="a.name" v-model="enabledAgents" @change="dirty = true" class="w-4 h-4 accent-cyan-500">
            <img v-if="a.avatar_url" :src="a.avatar_url" class="w-7 h-7 rounded-full object-cover">
            <div>
              <div class="text-sm text-white/90">{{ a.display }}</div>
              <div class="text-[10px] text-white/40">{{ a.name }}</div>
            </div>
          </label>
        </div>

        <div v-if="saveStatus" class="mt-4 text-sm" :class="saveStatus.ok ? 'text-green-400' : 'text-red-400'">{{ saveStatus.text }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted, watch } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, put } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const skills = ref([])
const loading = ref(false)
const selected = ref(null)
const allAgents = ref([])
const agentsLoading = ref(false)
const enabledAgents = ref([])
const dirty = ref(false)
const saving = ref(false)
const saveStatus = ref(null)

async function loadSkills() {
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

function selectSkill(s) {
  selected.value = s
  enabledAgents.value = [...(s.enabled_agents || [])]
  dirty.value = false
  saveStatus.value = null
  if (!allAgents.value.length) loadAgents()
}

async function saveAssign() {
  saving.value = true
  saveStatus.value = null
  const res = await put(`/api/skills/${selected.value.name}/agents`, { enabled_agents: enabledAgents.value })
  if (res?.ok) {
    saveStatus.value = { ok: true, text: '✅ 已儲存' }
    dirty.value = false
    // Update local skill data
    selected.value.enabled_agents = [...enabledAgents.value]
    const idx = skills.value.findIndex(s => s.name === selected.value.name)
    if (idx >= 0) skills.value[idx].enabled_agents = [...enabledAgents.value]
  } else {
    saveStatus.value = { ok: false, text: '❌ ' + (res?.detail || '儲存失敗') }
  }
  saving.value = false
}

watch(currentGroup, () => { loadSkills(); loadAgents() })
onMounted(loadSkills)
</script>
