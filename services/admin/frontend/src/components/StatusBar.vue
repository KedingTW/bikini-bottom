<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm flex-wrap sticky top-0 z-10">
    <slot />
    <span class="ml-auto text-white/70 text-xs">{{ lastUpdate }}</span>
    <span class="text-cyan-400 text-xs">{{ countdown }}s 後更新</span>
  </div>
</template>

<script setup>
defineProps({
  lastUpdate: { type: String, default: '載入中...' },
  countdown: { type: Number, default: 0 },
})
</script>
