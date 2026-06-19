import { ref, inject, watch, onMounted } from 'vue'
import { useApi } from './useApi.js'

export function useAgentList() {
  const { get } = useApi()
  const currentGroup = inject('currentGroup', ref('bikini-bottom'))
  const agents = ref([])
  const selectedAgent = ref(null)
  const loading = ref(false)

  async function loadAgents() {
    loading.value = true
    const res = await get(`/api/agents?group=${currentGroup.value}`)
    agents.value = res?.agents || []
    loading.value = false
    // Auto-select first if none selected
    if (!selectedAgent.value && agents.value.length) {
      selectedAgent.value = agents.value[0]
    } else if (selectedAgent.value) {
      // Re-find in case data refreshed
      const found = agents.value.find(a => a.name === selectedAgent.value.name)
      if (found) selectedAgent.value = found
      else selectedAgent.value = agents.value[0] || null
    }
  }

  function selectAgent(a) { selectedAgent.value = a }

  watch(currentGroup, () => { selectedAgent.value = null; loadAgents() })
  onMounted(() => { loadAgents(); window.addEventListener('group-changed', loadAgents) })

  return { agents, selectedAgent, loading, loadAgents, selectAgent, currentGroup }
}
