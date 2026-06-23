<template>
  <div class="flex h-full">
    <AgentListPanel :agents="agents" :selected="selectedAgent" :loading="loading" @select="$emit('select', $event)" />

    <!-- Detail area: hidden on mobile when no agent selected -->
    <div :class="selectedAgent ? '' : 'hidden md:block'"
      class="flex-1 overflow-y-auto p-4 sm:p-6">
      <!-- Mobile back button -->
      <button v-if="selectedAgent" @click="$emit('back')"
        class="md:hidden flex items-center gap-1 text-sm text-white/60 mb-4 -mt-1 active:text-white/80">
        <span>←</span> <span>返回角色列表</span>
      </button>

      <slot />
    </div>
  </div>
</template>

<script setup>
import AgentListPanel from './AgentListPanel.vue'

defineProps({
  agents: { type: Array, default: () => [] },
  selectedAgent: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})
defineEmits(['select', 'back'])
</script>
