<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm sticky top-0 z-10">
    <span class="font-medium">技能管理</span>
    <span class="text-white/40 text-xs">{{ skills.length }} 個技能</span>
    <button @click="load()" class="ml-auto bg-ocean-800 text-white border border-white/20 rounded px-3 py-1.5 text-sm hover:border-cyan-400/50">🔄 更新</button>
  </div>

  <div class="p-7">
    <div v-if="!skills.length" class="text-center py-20 text-white/50">
      <div class="text-4xl mb-3">🎯</div>
      <div>尚無可用技能</div>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="s in skills" :key="s.name" class="glass rounded-xl p-5">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-cyan-400 text-lg">🎯</span>
          <span class="font-medium text-base">{{ s.name }}</span>
        </div>
        <div class="text-sm text-white/60 line-clamp-2 mb-3">{{ s.description || '（無描述）' }}</div>
        <div class="text-xs text-white/40">已分配給 {{ getAssignedCount(s.name) }} 個角色</div>
      </div>
    </div>

    <!-- Assignment Section -->
    <div v-if="skills.length" class="mt-8">
      <h3 class="font-semibold text-cyan-300 mb-4">📋 技能分配總覽</h3>
      <div class="glass rounded-xl overflow-x-auto">
        <table class="w-full text-sm">
          <thead><tr class="bg-ocean-800/60">
            <th class="text-left px-4 py-2 font-semibold">角色</th>
            <th v-for="s in skills" :key="s.name" class="text-center px-3 py-2 font-semibold text-xs">{{ s.name }}</th>
          </tr></thead>
          <tbody>
            <tr v-for="a in agents" :key="a.name" class="border-t border-white/5">
              <td class="px-4 py-2 font-medium">{{ a.display }}</td>
              <td v-for="s in skills" :key="s.name" class="text-center px-3 py-2">
                <input type="checkbox" :checked="isAssigned(a.name, s.name)" @change="toggleAssign(a.name, s.name, $event.target.checked)" class="w-4 h-4 rounded">
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="flex items-center gap-3 mt-4">
        <button @click="publishAll()" class="bg-cyan-600 hover:bg-cyan-500 text-white px-5 py-2 rounded text-sm font-medium">🚀 全部發佈</button>
        <span v-if="publishStatus" class="text-sm" :class="publishStatus.ok ? 'text-green-400' : 'text-red-400'">{{ publishStatus.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useApi } from '../composables/useApi.js'
const { get, put, post } = useApi()
const currentGroup = inject('currentGroup', ref('bikini-bottom'))

const skills = ref([])
const agents = ref([])
const assignmentMap = ref({}) // { agentName: Set(skillNames) }
const publishStatus = ref(null)

function isAssigned(agent, skill) { return assignmentMap.value[agent]?.has(skill) || false }

function toggleAssign(agent, skill, checked) {
  if (!assignmentMap.value[agent]) assignmentMap.value[agent] = new Set()
  if (checked) assignmentMap.value[agent].add(skill)
  else assignmentMap.value[agent].delete(skill)
  // Save draft
  const assignments = [...(assignmentMap.value[agent] || [])].map(s => ({ skill_name: s, enabled: true }))
  put(`/api/skill-assignments/${agent}`, { assignments })
}

function getAssignedCount(skill) {
  return Object.values(assignmentMap.value).filter(s => s.has(skill)).length
}

async function publishAll() {
  publishStatus.value = null
  let count = 0
  for (const a of agents.value) {
    if (assignmentMap.value[a.name]?.size) {
      await post(`/api/skill-assignments/${a.name}/publish`)
      count++
    }
  }
  publishStatus.value = { ok: true, text: `✅ 已發佈 ${count} 個角色的技能` }
}

async function load() {
  const [sRes, aRes] = await Promise.all([get('/api/skills-registry'), get(`/api/agents?group=${currentGroup.value}`)])
  skills.value = sRes?.skills || []
  agents.value = aRes?.agents || []
  // Load assignments for each agent
  assignmentMap.value = {}
  for (const a of agents.value) {
    const res = await get(`/api/skill-assignments/${a.name}`)
    assignmentMap.value[a.name] = new Set((res?.assignments || []).map(x => x.skill_name))
  }
}

onMounted(load)
</script>
