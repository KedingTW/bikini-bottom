<template>
  <div class="flex flex-wrap gap-1.5 bg-ocean-800 border border-white/15 rounded px-2 py-1.5 min-h-[32px] cursor-text" @click="$refs.input.focus()">
    <span v-for="(tag, i) in modelValue" :key="i" class="inline-flex items-center gap-0.5 bg-cyan-600/20 text-cyan-300 text-[10px] px-1.5 py-0.5 rounded">
      {{ tag }}
      <button @click="remove(i)" class="text-cyan-400/60 hover:text-white ml-0.5">×</button>
    </span>
    <input ref="input" v-model="input" @keydown.enter.prevent="add" @keydown.backspace="onBackspace"
      class="flex-1 min-w-[60px] bg-transparent text-xs text-white outline-none placeholder-white/30" placeholder="輸入後 Enter">
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({ modelValue: { type: Array, default: () => [] } })
const emit = defineEmits(['update:modelValue'])
const input = ref('')

function add() {
  const v = input.value.trim()
  if (v && !props.modelValue.includes(v)) {
    emit('update:modelValue', [...props.modelValue, v])
  }
  input.value = ''
}

function remove(i) {
  const arr = [...props.modelValue]
  arr.splice(i, 1)
  emit('update:modelValue', arr)
}

function onBackspace() {
  if (!input.value && props.modelValue.length) {
    remove(props.modelValue.length - 1)
  }
}
</script>
