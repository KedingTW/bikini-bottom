<template>
  <button @click="$emit('update:modelValue', !modelValue)" type="button"
    class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0"
    :class="modelValue ? 'bg-cyan-600' : 'bg-white/20'">
    <span class="inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform"
      :class="modelValue ? 'translate-x-6' : 'translate-x-1'"></span>
  </button>
</template>

<script setup>
defineProps({ modelValue: { type: Boolean, default: false } })
defineEmits(['update:modelValue'])
</script>
