<template>
  <div class="w-full md:w-56 lg:w-64 shrink-0 border-r border-white/10 overflow-y-auto">
    <div class="p-3 border-b border-white/10">
      <h3 class="text-xs font-medium text-white/50 uppercase tracking-wider">選擇角色</h3>
    </div>
    <div v-if="loading" class="p-4 text-center text-white/50 text-sm">載入中...</div>
    <div v-else-if="!agents.length" class="p-4 text-center text-white/50 text-sm">無角色</div>
    <div v-else class="py-1">
      <button v-for="a in agents" :key="a.name" @click="$emit('select', a)"
        class="w-full flex items-center gap-2.5 px-3 py-2.5 text-left transition"
        :class="selected?.name === a.name ? 'bg-cyan-500/15 border-l-2 border-cyan-400' : 'hover:bg-white/5 border-l-2 border-transparent'">
        <img :src="'/avatar/' + a.name" class="w-8 h-8 rounded-full object-cover border border-white/20" @error="$event.target.style.display='none'">
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium truncate" :class="selected?.name === a.name ? 'text-cyan-300' : 'text-white/90'">{{ a.display }}</div>
          <div class="text-[10px] text-white/50 truncate">{{ a.role }}</div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  agents: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})
defineEmits(['select'])
</script>
