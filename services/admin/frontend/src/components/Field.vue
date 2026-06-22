<template>
  <div>
    <label class="flex items-center gap-1 text-[10px] text-white/50 mb-1">
      {{ label }}
      <span v-if="tip" class="relative group cursor-help">
        <span class="text-white/30">ⓘ</span>
        <span class="absolute bottom-full left-0 mb-1 px-2 py-1 bg-ocean-700 border border-white/20 rounded text-[10px] text-white/80 whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition z-50">{{ tip }}</span>
      </span>
    </label>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  tip: { type: String, default: '' }
})
</script>
