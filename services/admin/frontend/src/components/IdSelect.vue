<template>
  <div>
    <div class="flex flex-wrap gap-1.5 mb-2">
      <span v-for="id in modelValue" :key="id" class="inline-flex items-center gap-1 bg-cyan-600/20 text-cyan-300 text-sm px-2 py-1 rounded">
        {{ getLabel(id) }}
        <button @click="remove(id)" class="text-cyan-400/60 hover:text-white ml-0.5">×</button>
      </span>
    </div>
    <select @change="add($event.target.value); $event.target.value = ''" class="field-input">
      <option value="">+ 選擇{{ placeholder }}</option>
      <option v-for="opt in available" :key="opt.id" :value="opt.id">{{ opt.label }}</option>
    </select>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const available = computed(() => props.options.filter(o => !props.modelValue.includes(o.id)))

function getLabel(id) {
  const opt = props.options.find(o => o.id === id)
  return opt ? opt.label : id
}

function add(id) {
  if (id && !props.modelValue.includes(id)) {
    emit('update:modelValue', [...props.modelValue, id])
  }
}

function remove(id) {
  emit('update:modelValue', props.modelValue.filter(v => v !== id))
}
</script>

<style scoped>
.field-input {
  @apply w-full bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400/50;
}
</style>
