<template>
  <div>
    <div class="flex flex-wrap gap-1.5 mb-2">
      <span v-for="id in modelValue" :key="id" class="inline-flex items-center gap-1 text-sm px-2 py-1 rounded"
        :class="isLocked(id) ? 'bg-white/10 text-white/50' : 'bg-cyan-600/20 text-cyan-300'">
        <img v-if="getAvatar(id)" :src="getAvatar(id)" class="w-4 h-4 rounded-full">
        {{ getLabel(id) }}
        <span v-if="isLocked(id)" class="text-[10px] text-white/30 ml-1">🔒</span>
        <button v-else @click="remove(id)" type="button" class="text-cyan-400/60 hover:text-white ml-0.5">×</button>
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
  placeholder: { type: String, default: '' },
  lockedIds: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue'])

const available = computed(() => props.options.filter(o => !props.modelValue.some(v => String(v) === String(o.id))))

function isLocked(id) { return props.lockedIds.some(l => String(l) === String(id)) }

function getLabel(id) {
  const opt = props.options.find(o => String(o.id) === String(id))
  return opt ? opt.label : id
}

function getAvatar(id) {
  const opt = props.options.find(o => String(o.id) === String(id))
  return opt?.avatar || ''
}

function add(id) {
  if (id && !props.modelValue.some(v => String(v) === String(id))) {
    emit('update:modelValue', [...props.modelValue, id])
  }
}

function remove(id) {
  if (isLocked(id)) return
  emit('update:modelValue', props.modelValue.filter(v => String(v) !== String(id)))
}
</script>

<style scoped>
.field-input {
  @apply w-full bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400/50;
}
</style>
