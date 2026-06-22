<template>
  <div class="relative">
    <button @click="open = !open" type="button" class="flex items-center gap-2 bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm hover:border-white/30 w-full text-left">
      <span class="text-xl">{{ modelValue }}</span>
      <span class="text-xs text-white/40 ml-auto">▾</span>
    </button>
    <div v-if="open" class="absolute top-full left-0 mt-1 z-50 bg-ocean-700 border border-white/20 rounded-lg shadow-xl w-72 max-h-[320px] flex flex-col">
      <input v-model="search" placeholder="搜尋或自行輸入 emoji..." class="w-full bg-ocean-800 border-b border-white/15 rounded-t-lg px-3 py-2 text-sm text-white focus:outline-none" @keydown.enter="selectCustom">
      <div class="flex gap-1 px-2 py-1.5 border-b border-white/10 overflow-x-auto no-scrollbar">
        <button v-for="g in groups" :key="g.name" @click="activeGroup = g.name"
          class="text-lg px-1.5 py-0.5 rounded shrink-0" :class="activeGroup === g.name ? 'bg-cyan-600/30' : 'hover:bg-white/10'" :title="g.name">{{ g.icon }}</button>
      </div>
      <div class="flex-1 overflow-y-auto p-2">
        <div class="grid grid-cols-8 gap-0.5">
          <button v-for="e in filteredEmojis" :key="e" @click="select(e)" type="button" class="text-xl p-1.5 rounded hover:bg-white/10 text-center">{{ e }}</button>
        </div>
        <div v-if="!filteredEmojis.length" class="text-center text-sm text-white/40 py-4">無結果</div>
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
const activeGroup = ref('比奇堡')

const groups = [
  { name: '比奇堡', icon: '🏝️', emojis: ['🐌','🧽','⭐','🐡','🦑','🐿️','🦞','🐋','🐚','🔥','👀','🤔','⚡','🆗','😱','👨‍💻','📋','🪨','🍔','🏝️','🌊','🎣','⚓','🪸','🐠','🦀','🐙','🫧'] },
  { name: '表情', icon: '😀', emojis: ['😀','😂','🤣','😅','😊','😎','🥳','😢','😡','🤯','🫠','😱','🥹','😤','🫡','🤝','👋','✋','👍','👎','👏','🙏','💪','🫶','🤌','✌️','🤞','🖐️'] },
  { name: '符號', icon: '✅', emojis: ['✅','❌','⚠️','❓','❗','💡','🔔','📌','📎','🔗','🏷️','✏️','📝','📋','🗂️','📂','📁','📄','📊','📈','📉','🔒','🔑','🛡️','⭕','❎','☑️','✔️'] },
  { name: '工具', icon: '🔧', emojis: ['🔧','🛠️','⚙️','🔩','🔨','💻','🖥️','⌨️','📱','🖨️','💾','📀','🔌','🔋','📡','🛜','🤖','🧠','💡','🔬','🧪','📐','📏','✂️','🗑️','📦','🚀','🎯'] },
  { name: '時間', icon: '⏰', emojis: ['⏰','⏱️','⏳','🕐','🕑','🕒','🕓','🕔','🕕','🕖','🕗','🕘','🕙','🕚','🕛','📅','🗓️','📆','🌅','🌇','🌃','🌙','☀️','⭐','🌟','💫','✨','🎆'] },
  { name: '動物', icon: '🐱', emojis: ['🐱','🐶','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐸','🐵','🐔','🐧','🐦','🦆','🦅','🐝','🐛','🦋','🐌','🐙','🦑','🐠','🐳'] },
  { name: '食物', icon: '🍔', emojis: ['🍔','🍟','🌮','🍕','🍣','🍜','🍝','🍛','🍲','🍱','🍙','🍘','🍡','🍧','🍰','🎂','🍪','☕','🍵','🧋','🥤','🍺','🍷','🧃','🍎','🍊','🍋','🍉'] },
  { name: '其他', icon: '🎨', emojis: ['🎨','🎭','🎪','🎠','🎡','🎢','🏆','🥇','🥈','🥉','🎖️','🏅','🎗️','🎫','🎟️','🎪','♠️','♥️','♦️','♣️','🃏','🀄','🎲','🎮','🕹️','🎯','🎳','🎰'] },
]

const filteredEmojis = computed(() => {
  if (search.value) {
    const all = groups.flatMap(grp => grp.emojis)
    return all.filter(e => e.includes(search.value))
  }
  const found = groups.find(grp => grp.name === activeGroup.value)
  return found ? found.emojis : []
})

function select(e) { emit('update:modelValue', e); open.value = false; search.value = '' }
function selectCustom() { if (search.value.trim()) { emit('update:modelValue', search.value.trim()); open.value = false; search.value = '' } }
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
