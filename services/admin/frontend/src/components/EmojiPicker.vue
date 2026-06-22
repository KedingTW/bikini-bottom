<template>
  <div class="relative">
    <button @click="open = !open" class="w-full flex items-center gap-2 bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm text-left hover:border-white/30">
      <span class="text-lg">{{ modelValue }}</span>
      <span class="text-xs text-white/40 ml-auto">▾</span>
    </button>
    <div v-if="open" class="absolute top-full left-0 mt-1 z-50 bg-ocean-700 border border-white/20 rounded-lg shadow-xl p-2 w-64">
      <input v-model="search" placeholder="搜尋或自行輸入..." class="w-full bg-ocean-800 border border-white/15 rounded px-2 py-1.5 text-sm text-white mb-2 focus:outline-none focus:border-cyan-400/50" @keydown.enter="selectCustom">
      <div class="grid grid-cols-8 gap-0.5 max-h-40 overflow-y-auto">
        <button v-for="e in filtered" :key="e" @click="select(e)" class="text-xl p-1 rounded hover:bg-white/10 text-center">{{ e }}</button>
      </div>
    </div>
  </div>
  <div v-if="open" class="fixed inset-0 z-40" @click="open = false"></div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ modelValue: { type: String, default: '😀' } })
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const search = ref('')

const emojis = ['😀','😂','🤔','😅','👍','👎','✅','❌','🔧','✍️','📋','🚫','⏳','🎉','💡','🔥','❤️','⭐','🚀','💰','🎯','📌','🔔','📢','🏠','🤖','📊','📈','💬','🙏','👀','🎊','⚡','🌟','💪','🧠','📝','🔍','🛠️','📦','🎵','☕','🌈','🔒','🔑','📅','⏰','🗓️','💎','🌊','🍔','🧽','⬆️','⬇️','↩️','🔄','➡️','⬅️','✋','👋','🤝','🫡','😎','🥳','😢','😡','🤯','🫠','💤','🌙','☀️','🌤️','❄️','🔵','🟢','🟡','🔴','⚪','🟠','🟣','⚫','🏆','🎖️','🥇','🥈','🎮','🎨','📸','🎬','💻','📱','🖥️','⌨️','🗂️','📂','📁','📄']

const filtered = computed(() => {
  if (!search.value) return emojis
  return emojis.filter(e => e.includes(search.value))
})

function select(e) { emit('update:modelValue', e); open.value = false; search.value = '' }
function selectCustom() { if (search.value.trim()) { emit('update:modelValue', search.value.trim()); open.value = false; search.value = '' } }
</script>
