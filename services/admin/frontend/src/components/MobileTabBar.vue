<template>
  <nav class="fixed bottom-0 left-0 right-0 z-40 glass-darker border-t border-white/10 safe-bottom">
    <div class="flex items-stretch justify-around">
      <router-link v-for="tab in visibleTabs" :key="tab.path" :to="tab.path"
        class="flex flex-col items-center justify-center py-2 px-1 flex-1 min-w-0 transition"
        :class="isActive(tab.path) ? 'text-cyan-400' : 'text-white/60 active:text-white/80'">
        <span class="text-lg">{{ tab.icon }}</span>
        <span class="text-[10px] mt-0.5 truncate w-full text-center">{{ tab.label }}</span>
      </router-link>

      <!-- More button -->
      <button @click="moreOpen = !moreOpen"
        class="flex flex-col items-center justify-center py-2 px-1 flex-1 min-w-0 transition"
        :class="moreOpen ? 'text-cyan-400' : 'text-white/60 active:text-white/80'">
        <span class="text-lg">⋯</span>
        <span class="text-[10px] mt-0.5">更多</span>
      </button>
    </div>

    <!-- More menu popup -->
    <transition name="slide-up">
      <div v-if="moreOpen" class="absolute bottom-full left-0 right-0 glass-darker border-t border-white/10 rounded-t-xl shadow-2xl max-h-[60vh] overflow-y-auto">
        <div class="grid grid-cols-4 gap-1 p-4">
          <router-link v-for="item in moreItems" :key="item.path" :to="item.path"
            class="flex flex-col items-center gap-1.5 p-3 rounded-xl transition"
            :class="isActive(item.path) ? 'bg-cyan-500/15 text-cyan-400' : 'text-white/70 active:bg-white/10'"
            @click="moreOpen = false">
            <span class="text-xl">{{ item.icon }}</span>
            <span class="text-[10px] text-center leading-tight">{{ item.label }}</span>
          </router-link>
        </div>
      </div>
    </transition>
  </nav>

  <!-- Overlay to close more menu -->
  <div v-if="moreOpen" class="fixed inset-0 z-30" @click="moreOpen = false"></div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  role: { type: String, default: 'viewer' }
})

const route = useRoute()
const router = useRouter()
const moreOpen = ref(false)

// Close on route change
router.afterEach(() => { moreOpen.value = false })

// Primary tabs shown in bottom bar
const primaryTabs = [
  { path: '/', icon: '🏠', label: '總覽', admin: false },
  { path: '/agent-config', icon: '🤖', label: '角色', admin: true },
  { path: '/metrics', icon: '📊', label: '監控', admin: false },
  { path: '/costs', icon: '💰', label: '成本', admin: false },
]

// Secondary items in "more" menu
const secondaryItems = [
  { path: '/alerts', icon: '🔔', label: '異常通知', admin: false },
  { path: '/logs', icon: '📋', label: 'Log', admin: true },
  { path: '/messaging', icon: '📢', label: '推送', admin: true },
  { path: '/members', icon: '👥', label: '成員', admin: true },
  { path: '/threads', icon: '📌', label: '討論串', admin: true },
  { path: '/thread-analytics', icon: '📈', label: '分析', admin: true },
  { path: '/deploy', icon: '🚀', label: '部署', admin: true },
  { path: '/system', icon: '🖥️', label: '系統', admin: false },
  { path: '/api-keys', icon: '🔑', label: 'API Key', admin: true },
  { path: '/users', icon: '👤', label: '使用者', admin: true },
]

const visibleTabs = computed(() =>
  primaryTabs.filter(t => !t.admin || props.role === 'admin')
)

const moreItems = computed(() =>
  secondaryItems.filter(t => !t.admin || props.role === 'admin')
)

function isActive(path) { return route.path === path }
</script>

<style scoped>
.safe-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
.slide-up-enter-active, .slide-up-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(8px);
  opacity: 0;
}
</style>
