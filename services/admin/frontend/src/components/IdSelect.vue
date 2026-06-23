<template>
  <div>
    <!-- Selected tags -->
    <div class="flex flex-wrap gap-1.5 mb-2" v-if="modelValue.length">
      <span v-for="id in modelValue" :key="id" class="inline-flex items-center gap-1 text-sm px-2 py-1 rounded"
        :class="isLocked(id) ? 'bg-white/10 text-white/50' : 'bg-cyan-600/20 text-cyan-300'">
        <img v-if="getAvatar(id)" :src="getAvatar(id)" class="w-4 h-4 rounded-full object-cover">
        <span v-else-if="getColor(id)" class="w-3 h-3 rounded-full shrink-0" :style="{background: getColor(id)}"></span>
        {{ getLabel(id) }}
        <span v-if="isLocked(id)" class="text-[10px] text-white/30 ml-1">🔒</span>
        <button v-else @click="remove(id)" type="button" class="text-cyan-400/60 hover:text-white ml-0.5">×</button>
      </span>
    </div>
    <!-- Custom dropdown trigger -->
    <div class="relative">
      <button @click="open = !open" type="button" class="w-full flex items-center bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm text-white/50 hover:border-white/30 text-left">
        + 選擇{{ placeholder }}
        <span class="ml-auto text-xs">▾</span>
      </button>
      <!-- Dropdown panel -->
      <div v-if="open" class="absolute top-full left-0 right-0 mt-1 z-50 bg-ocean-700 border border-white/20 rounded-lg shadow-xl max-h-48 overflow-y-auto">
        <div v-if="!available.length" class="px-3 py-2 text-sm text-white/40">無可選項目</div>
        <button v-for="opt in available" :key="opt.id" @click="add(opt.id)" type="button"
          class="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-white/10 transition">
          <img v-if="opt.avatar" :src="opt.avatar" class="w-5 h-5 rounded-full object-cover shrink-0">
          <span v-else-if="opt.color" class="w-4 h-4 rounded-full shrink-0" :style="{background: opt.color}"></span>
          <span class="truncate text-white/90">{{ opt.label }}</span>
        </button>
      </div>
    </div>
    <!-- Click outside -->
    <div v-if="open" class="fixed inset-0 z-40" @click="open = false"></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  lockedIds: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue'])
const open = ref(false)

const available = computed(() => props.options.filter(o => !props.modelValue.some(v => String(v) === String(o.id))))

function isLocked(id) { return props.lockedIds.some(l => String(l) === String(id)) }
function getLabel(id) { const opt = props.options.find(o => String(o.id) === String(id)); return opt ? opt.label : id }
function getAvatar(id) { const opt = props.options.find(o => String(o.id) === String(id)); return opt?.avatar || '' }
function getColor(id) { const opt = props.options.find(o => String(o.id) === String(id)); return opt?.color || '' }

function add(id) {
  if (id && !props.modelValue.some(v => String(v) === String(id))) {
    emit('update:modelValue', [...props.modelValue, id])
  }
  open.value = false
}

function remove(id) {
  if (isLocked(id)) return
  emit('update:modelValue', props.modelValue.filter(v => String(v) !== String(id)))
}
</script>
