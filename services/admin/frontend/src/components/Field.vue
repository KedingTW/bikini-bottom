<template>
  <div>
    <label class="flex items-center gap-1 text-sm text-white/70 mb-1.5">
      {{ label }}
      <span v-if="tip" class="relative group cursor-help">
        <span class="text-white/30 text-xs">ⓘ</span>
        <span class="absolute bottom-full left-0 mb-1 px-2 py-1 bg-ocean-700 border border-white/20 rounded text-xs text-white/80 whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition z-50 max-w-[250px] whitespace-normal">{{ tip }}</span>
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
