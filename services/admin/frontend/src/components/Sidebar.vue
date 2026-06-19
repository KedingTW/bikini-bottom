<template>
  <nav :class="collapsed ? 'w-14' : 'w-48'" class="glass-darker border-r border-white/10 flex flex-col shrink-0 transition-all duration-300 relative overflow-visible z-20 h-full">
    <button @click="collapsed = !collapsed"
      class="absolute -right-3 top-3 w-7 h-7 bg-ocean-700 border border-white/20 rounded-full text-white/70 hover:text-white hover:bg-ocean-600 flex items-center justify-center text-xs z-10">
      {{ collapsed ? '›' : '‹' }}
    </button>

    <!-- Group Switcher -->
    <div class="px-3 pt-3 pb-2 border-b border-white/10" v-show="!collapsed">
      <button @click="groupOpen = !groupOpen" class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-cyan-600/20 border border-cyan-400/30 hover:bg-cyan-600/30 transition">
        <img v-if="currentGroupImage" :src="currentGroupImage" class="w-6 h-6 rounded object-cover">
        <span v-else class="text-lg">{{ currentGroupIcon }}</span>
        <span class="flex-1 text-left text-sm font-medium text-cyan-200 truncate">{{ currentGroupDisplay }}</span>
        <span class="text-xs text-cyan-400">▾</span>
      </button>
      <div v-if="groupOpen" class="mt-1 bg-ocean-700 border border-white/15 rounded-lg shadow-xl overflow-hidden">
        <button v-for="g in groups" :key="g.id" @click="selectGroup(g.id)"
          :class="g.id === currentGroup ? 'bg-cyan-600/20 text-cyan-300' : 'text-white/80 hover:bg-white/10'"
          class="w-full flex items-center gap-2 px-3 py-2 text-sm transition">
          <img v-if="g.image" :src="g.image" class="w-5 h-5 rounded object-cover">
          <span v-else>{{ g.icon }}</span>
          <span>{{ g.display }}</span>
          <span v-if="g.id === currentGroup" class="ml-auto text-xs">✓</span>
        </button>
      </div>
    </div>
    <!-- Collapsed: just show icon -->
    <div v-show="collapsed" class="px-2 pt-3 pb-2 border-b border-white/10 text-center">
      <span class="text-lg" :title="currentGroupDisplay">{{ currentGroupIcon }}</span>
    </div>

    <div class="py-3 flex-1 overflow-y-auto">
      <template v-for="group in visibleGroups" :key="group.label">
        <!-- Divider -->
        <div v-if="group.divider" class="my-3 mx-4 border-t-2 border-cyan-400/30" v-show="!collapsed"></div>
        <div v-if="group.divider && collapsed" class="my-3 mx-2 border-t-2 border-cyan-400/30"></div>
        <!-- Group label -->
        <div v-if="group.label" class="px-5 pt-4 pb-1 text-[10px] uppercase tracking-wider text-white/60" v-show="!collapsed">{{ group.label }}</div>
        <router-link v-for="item in group.items" :key="item.path" :to="item.path"
          class="flex items-center gap-3 px-5 py-2 text-sm border-l-[3px] transition"
          :class="isActive(item.path) ? 'text-cyan-400 bg-cyan-500/10 border-cyan-400' : 'text-white/80 hover:text-white hover:bg-white/5 border-transparent'">
          <span class="text-base w-5 text-center">{{ item.icon }}</span>
          <span v-show="!collapsed" class="truncate">{{ item.label }}</span>
        </router-link>
      </template>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({ role: { type: String, default: 'viewer' }, groups: { type: Array, default: () => [] } })
const route = useRoute()
const collapsed = ref(false)
const groupOpen = ref(false)
const currentGroup = inject('currentGroup', ref('bikini-bottom'))
const onGroupChange = inject('onGroupChange', () => {})

const currentGroupDisplay = computed(() => props.groups.find(g => g.id === currentGroup.value)?.display || currentGroup.value)
const currentGroupIcon = computed(() => props.groups.find(g => g.id === currentGroup.value)?.icon || '🏝️')
const currentGroupImage = computed(() => props.groups.find(g => g.id === currentGroup.value)?.image || '')

function selectGroup(id) {
  currentGroup.value = id
  onGroupChange()
  groupOpen.value = false
}

const navGroups = [
  { label: '', items: [
    { path: '/', icon: '🏠', label: '總覽', admin: false },
  ]},
  { label: '伺服器管理', items: [
    { path: '/agent-config', icon: '🤖', label: '角色配置', admin: true },
    { path: '/metrics', icon: '📊', label: '資源監控', admin: false },
    { path: '/alerts', icon: '🔔', label: '異常通知', admin: false },
    { path: '/logs', icon: '📋', label: 'Log 搜尋', admin: true },
    { path: '/members', icon: '👥', label: '成員管理', admin: true, dcOnly: true },
    { path: '/threads', icon: '📌', label: '討論串管理', admin: true, dcOnly: true },
    { path: '/thread-analytics', icon: '📈', label: '討論串分析', admin: true, dcOnly: true },
    { path: '/messaging', icon: '📢', label: '訊息推送', admin: true, dcOnly: true },
  ]},
  { label: '', divider: true, items: [] },
  { label: '共用功能', items: [
    { path: '/costs', icon: '💰', label: '成本監控', admin: false },
    { path: '/deploy', icon: '🚀', label: '部署管理', admin: true },
    { path: '/system', icon: '🖥️', label: '系統資源', admin: false },
    { path: '/api-keys', icon: '🔑', label: 'API Key', admin: true },
    { path: '/users', icon: '👤', label: '使用者', admin: true },
  ]},
]

const isWecom = computed(() => currentGroup.value === 'keding-wecom')

const visibleGroups = computed(() => {
  return navGroups.map(g => {
    if (g.divider) return { label: '', divider: true, items: [] }
    return {
      label: g.label,
      items: g.items.filter(item => {
        if (item.admin && props.role !== 'admin') return false
        if (item.dcOnly && isWecom.value) return false
        return true
      })
    }
  }).filter(g => g.divider || g.items.length > 0)
})

function isActive(path) { return route.path === path }
</script>
