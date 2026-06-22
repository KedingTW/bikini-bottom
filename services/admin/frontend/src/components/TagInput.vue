<template>
  <div class="flex flex-wrap gap-1.5 bg-ocean-800 border border-white/15 rounded px-3 py-2 min-h-[38px] cursor-text" @click="inputEl?.focus()">
    <span v-for="(tag, i) in modelValue" :key="i" class="inline-flex items-center gap-1 bg-cyan-600/20 text-cyan-300 text-sm px-2 py-0.5 rounded">
      {{ tag }}
      <button @click="remove(i)" type="button" class="text-cyan-400/60 hover:text-white">×</button>
    </span>
    <input ref="inputEl" v-model="inputText" @keydown.enter.prevent="add" @keydown.backspace="onBackspace"
      class="flex-1 min-w-[80px] bg-transparent text-sm text-white outline-none placeholder-white/30" placeholder="輸入後按 Enter">
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({ modelValue: { type: Array, default: () => [] } })
const emit = defineEmits(['update:modelValue'])
const inputEl = ref(null)
const inputText = ref('')

function add() {
  const v = inputText.value.trim()
  if (v && !props.modelValue.includes(v)) {
    emit('update:modelValue', [...props.modelValue, v])
  }
  inputText.value = ''
}

function remove(i) {
  const arr = [...props.modelValue]
  arr.splice(i, 1)
  emit('update:modelValue', arr)
}

function onBackspace() {
  if (!inputText.value && props.modelValue.length) {
    remove(props.modelValue.length - 1)
  }
}
</script>
