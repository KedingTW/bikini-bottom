<template>
  <!-- Sub Tab Bar (above main tab, dynamic based on active main tab) -->
  <div v-if="activeSubItems.length" class="fixed bottom-[calc(56px+env(safe-area-inset-bottom,0px))] left-0 right-0 z-40 glass-darker border-t border-white/5">
    <div class="flex items-stretch overflow-x-auto no-scrollbar">
      <router-link v-for="item in activeSubItems" :key="item.path" :to="item.path"
        class="flex items-center gap-1.5 px-4 py-2.5 text-xs whitespace-nowrap transition shrink-0"
        :class="route.path === item.path ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-white/60'">
        <span>{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </router-link>
    </div>
  </div>

  <!-- Main Tab Bar (fixed bottom) -->
  <nav class="fixed bottom-0 left-0 right-0 z-40 glass-darker border-t border-white/10 safe-bottom">
    <div class="flex items-stretch justify-around">
      <button v-for="tab in mainTabs" :key="tab.id" @click="selectMainTab(tab)"
        class="flex flex-col items-center justify-center py-2 px-1 flex-1 min-w-0 transition"
        :class="[
          activeMainTab === tab.id ? 'text-cyan-400' : 'text-white/60 active:text-white/80',
          tab.id === 'home' ? '-mt-2' : ''
        ]">
        <span :class="tab.id === 'home' ? 'text-2xl' : 'text-lg'">{{ tab.icon }}</span>
        <span class="text-[10px] mt-0.5">{{ tab.label }}</span>
      </button>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  role: { type: String, default: 'viewer' }
})

const route = useRoute()
const router = useRouter()

const mainTabs = [
  { id: 'agent', icon: '🤖', label: '角色管理' },
  { id: 'monitor', icon: '📊', label: '監控' },
  { id: 'home', icon: '🏠', label: '總覽' },
  { id: 'service', icon: '📢', label: '服務管理' },
  { id: 'more', icon: '⋯', label: '更多' },
]

const subTabs = {
  agent: [],
  monitor: [
    { path: '/metrics', icon: '📊', label: '資源', admin: false },
    { path: '/costs', icon: '💰', label: '成本', admin: false },
    { path: '/alerts', icon: '🔔', label: '異常通知', admin: false },
  ],
  home: [],
  service: [
    { path: '/messaging', icon: '📢', label: '推送', admin: true },
    { path: '/members', icon: '👥', label: '成員', admin: true },
    { path: '/threads', icon: '📌', label: '討論串', admin: true },
    { path: '/thread-analytics', icon: '📈', label: '分析', admin: true },
  ],
  more: [
    { path: '/logs', icon: '📋', label: '日誌', admin: true },
    { path: '/deploy', icon: '🚀', label: '部署', admin: true },
    { path: '/system', icon: '🖥️', label: '系統', admin: false },
    { path: '/users', icon: '👤', label: '使用者', admin: true },
    { path: '/knowledge', icon: '🧠', label: '知識庫', admin: true },
    { path: '/api-keys', icon: '🔑', label: '金鑰', admin: true },
  ],
}

// Determine active main tab from current route
const activeMainTab = ref('home')

function findMainTabForRoute(path) {
  if (path === '/agent-config') return 'agent'
  for (const [tabId, items] of Object.entries(subTabs)) {
    if (items.some(item => item.path === path)) return tabId
  }
  return 'home'
}

// Sync active main tab with route
watch(() => route.path, (path) => {
  activeMainTab.value = findMainTabForRoute(path)
}, { immediate: true })

const activeSubItems = computed(() => {
  const items = subTabs[activeMainTab.value] || []
  return items.filter(item => !item.admin || props.role === 'admin')
})

function selectMainTab(tab) {
  activeMainTab.value = tab.id
  if (tab.id === 'home') {
    router.push('/')
    return
  }
  if (tab.id === 'agent') {
    router.push('/agent-config')
    return
  }
  // Navigate to first sub item
  const items = subTabs[tab.id]?.filter(t => !t.admin || props.role === 'admin') || []
  if (items.length) {
    router.push(items[0].path)
  }
}
</script>

<style scoped>
.safe-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
