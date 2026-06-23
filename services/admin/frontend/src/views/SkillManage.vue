<template>
  <AgentDetailLayout :agents="agents" :selected-agent="selectedAgent" :loading="loading" @select="onSelect" @back="selectedAgent = null">
    <div v-if="!selectedAgent" class="text-center py-20 text-white/50 hidden md:block">
        <div class="text-3xl mb-2">📚</div>
        <div>請選擇角色查看 Skill 配置</div>
      </div>

      <div v-if="selectedAgent">
        <h2 class="text-lg font-semibold mb-5">{{ selectedAgent.display }} — 技能配置（{{ selectedAgent.skills_meta?.length || 0 }}）</h2>

        <div v-if="!selectedAgent.skills_meta?.length" class="text-white/50 text-sm py-4">尚無技能</div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div v-for="s in selectedAgent.skills_meta" :key="s.name"
            class="bg-ocean-800/50 rounded-lg px-4 py-3 cursor-pointer hover:bg-ocean-800/70 transition border border-white/5 hover:border-cyan-400/20"
            @click="viewSkill(s.name)">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-cyan-400">🧠</span>
              <span class="font-medium text-sm">{{ s.name }}</span>
            </div>
            <div v-if="s.description" class="text-xs text-white/60 line-clamp-2">{{ s.description }}</div>
          </div>
        </div>
      </div>

    <!-- Skill Viewer -->
    <div v-if="fileView" class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="fileView = null">
      <div class="bg-ocean-700 rounded-xl w-full max-w-3xl flex flex-col shadow-2xl" style="max-height: 80vh;">
        <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between font-semibold shrink-0">
          <span class="truncate">{{ fileView.filename }}</span>
          <button @click="fileView = null" class="text-2xl text-white/60 hover:text-white shrink-0 ml-2">&times;</button>
        </div>
        <div class="px-6 py-4 overflow-y-auto flex-1">
          <pre class="text-xs leading-relaxed whitespace-pre-wrap break-words text-white/90 bg-black/30 p-4 rounded-lg">{{ fileView.content }}</pre>
        </div>
      </div>
    </div>
  </AgentDetailLayout>
</template>

<script setup>
import { ref } from 'vue'
import { useAgentList } from '../composables/useAgentList.js'
import { useApi } from '../composables/useApi.js'
import AgentDetailLayout from '../components/AgentDetailLayout.vue'

const { get } = useApi()
const { agents, selectedAgent, loading, selectAgent } = useAgentList()
const fileView = ref(null)

function onSelect(a) { selectAgent(a) }

async function viewSkill(skillName) {
  const res = await get(`/api/agents/${selectedAgent.value.name}/skills/${skillName}`)
  if (res?.content) fileView.value = { filename: res.filename || skillName, content: res.content }
  else fileView.value = { filename: skillName, content: '(無 SKILL.md 內容)' }
}
</script>
