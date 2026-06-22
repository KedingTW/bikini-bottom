<template>
  <button @click="$emit('update:modelValue', !modelValue)" type="button"
    class="w-9 h-5 rounded-full transition relative"
    :class="modelValue ? 'bg-cyan-600' : 'bg-white/20'">
    <span class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform"
      :class="modelValue ? 'translate-x-4' : 'translate-x-0.5'"></span>
  </button>
</template>

<script setup>
defineProps({ modelValue: { type: Boolean, default: false } })
defineEmits(['update:modelValue'])
</script>
