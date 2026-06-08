<template>
  <nav :class="collapsed ? 'w-14' : 'w-48'" class="glass-darker border-r border-white/10 flex flex-col shrink-0 transition-all duration-300 relative overflow-visible z-20">
    <button @click="collapsed = !collapsed"
      class="absolute -right-3 top-3 w-7 h-7 bg-ocean-700 border border-white/20 rounded-full text-white/70 hover:text-white hover:bg-ocean-600 flex items-center justify-center text-xs z-10">
      {{ collapsed ? '›' : '‹' }}
    </button>
    <div class="py-4 flex-1">
      <router-link v-for="item in visibleItems" :key="item.path" :to="item.path"
        class="flex items-center gap-3 px-5 py-3 text-sm border-l-[3px] transition"
        :class="isActive(item.path) ? 'text-cyan-400 bg-cyan-500/10 border-cyan-400' : 'text-white/80 hover:text-white hover:bg-white/5 border-transparent'">
        <span class="text-lg w-5 text-center">{{ item.icon }}</span>
        <span v-show="!collapsed">{{ item.label }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({ role: { type: String, default: 'viewer' } })

const route = useRoute()
const collapsed = ref(false)

const navItems = [
  { path: '/', icon: '🏠', label: '總覽', requireAdmin: false },
  { path: '/metrics', icon: '📊', label: '資源監控', requireAdmin: false },
  { path: '/costs', icon: '💰', label: '成本監控', requireAdmin: false },
  { path: '/alerts', icon: '🔔', label: '告警紀錄', requireAdmin: false },
  { path: '/discord', icon: '🎮', label: 'Discord', requireAdmin: true },
  { path: '/users', icon: '👥', label: '使用者管理', requireAdmin: true },
]

const visibleItems = computed(() =>
  navItems.filter(item => !item.requireAdmin || props.role === 'admin')
)

function isActive(path) {
  return route.path === path
}
</script>
