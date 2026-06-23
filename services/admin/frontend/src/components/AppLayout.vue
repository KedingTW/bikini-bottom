<template>
  <!-- Top Header -->
  <header class="glass-darker sticky top-0 z-50 border-b border-white/10 px-4 sm:px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-2 sm:gap-3">
      <!-- Mobile hamburger -->
      <button @click="drawerOpen = true" class="md:hidden p-1.5 rounded-lg hover:bg-white/10 text-white/80">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
      </button>
      <img src="/header.png" alt="Logo" class="h-7">
    </div>
    <h1 class="text-base sm:text-lg font-semibold whitespace-nowrap truncate flex-1 text-center mx-2">
      <span class="hidden sm:inline">{{ currentGroupDisplay }} - </span>{{ pageTitle }}
    </h1>
    <div class="relative flex items-center gap-2 text-sm">
      <button @click="menuOpen = !menuOpen" class="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 rounded-lg hover:bg-white/10 transition text-white/90">
        <span class="hidden sm:inline">👤 {{ userName }}({{ userId }})</span>
        <span class="sm:hidden">👤</span>
        <span class="text-xs">▾</span>
      </button>
      <!-- Dropdown -->
      <div v-if="menuOpen" class="absolute right-0 top-full mt-1 w-40 bg-ocean-700 border border-white/15 rounded-lg shadow-xl overflow-hidden z-50">
        <button @click="showPwDialog = true; menuOpen = false" class="w-full text-left px-4 py-2.5 text-sm text-white hover:bg-white/10 transition">🔑 修改密碼</button>
        <a href="/logout" class="block px-4 py-2.5 text-sm text-white hover:bg-white/10 transition">🚪 登出</a>
      </div>
    </div>
  </header>

  <!-- Click outside to close menu -->
  <div v-if="menuOpen" class="fixed inset-0 z-40" @click="menuOpen = false"></div>

  <!-- Mobile Drawer -->
  <div v-if="drawerOpen" class="fixed inset-0 z-50 md:hidden" @click="drawerOpen = false">
    <div class="absolute inset-y-0 left-0 w-64 glass-darker border-r border-white/10 shadow-2xl" @click.stop>
      <div class="p-4 border-b border-white/10 flex items-center justify-between">
        <img src="/header.png" alt="Logo" class="h-6">
        <button @click="drawerOpen = false" class="text-white/60 hover:text-white text-xl">&times;</button>
      </div>
      <!-- Server switcher -->
      <div class="p-3 border-b border-white/10">
        <div class="text-xs text-white/50 uppercase mb-2">伺服器</div>
        <button v-for="g in groups" :key="g.id" @click="currentGroup = g.id; onGroupChange(); drawerOpen = false"
          class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm mb-1 transition"
          :class="g.id === currentGroup ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-400/30' : 'text-white/80 hover:bg-white/10'">
          <span>{{ g.icon }}</span><span>{{ g.display }}</span>
          <span v-if="g.id === currentGroup" class="ml-auto text-xs">✓</span>
        </button>
      </div>
      <!-- Quick links -->
      <div class="p-3">
        <div class="text-xs text-white/50 uppercase mb-2">快速連結</div>
        <router-link to="/users" @click="drawerOpen = false" class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm text-white/80 hover:bg-white/10">
          <span>👤</span><span>使用者管理</span>
        </router-link>
      </div>
    </div>
  </div>

  <div class="flex h-[calc(100vh-60px)]">
    <!-- Desktop sidebar (hidden on mobile) -->
    <div class="hidden md:block">
      <Sidebar :role="userRole" :groups="groups" />
    </div>

    <div class="flex-1 flex flex-col overflow-hidden">
      <main class="flex-1 overflow-y-auto pb-28 md:pb-0" id="main-scroll">
        <slot />
      </main>
      <img class="hidden md:block w-full max-h-12 object-contain bg-[#111827] py-2 shrink-0" src="/footer.png" alt="Footer">
    </div>
  </div>

  <!-- Mobile Bottom Tab Bar (hidden on desktop) -->
  <div class="block md:hidden">
    <MobileTabBar :role="userRole" />
  </div>

  <!-- Change Password Dialog -->
  <div v-if="showPwDialog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showPwDialog = false">
    <div class="bg-ocean-700 rounded-xl w-full max-w-sm p-6 shadow-2xl border border-white/10">
      <h3 class="text-lg font-semibold mb-4">🔑 修改密碼</h3>
      <div class="mb-4">
        <label class="block text-sm text-white/70 mb-1">舊密碼</label>
        <input v-model="pwForm.oldPassword" type="password" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white focus:outline-none focus:border-cyan-400/60">
      </div>
      <div class="mb-4">
        <label class="block text-sm text-white/70 mb-1">新密碼</label>
        <input v-model="pwForm.newPassword" type="password" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white focus:outline-none focus:border-cyan-400/60">
      </div>
      <div class="mb-4">
        <label class="block text-sm text-white/70 mb-1">確認新密碼</label>
        <input v-model="pwForm.confirmPassword" type="password" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white focus:outline-none focus:border-cyan-400/60">
      </div>
      <div v-if="pwError" class="mb-3 text-sm text-red-400">{{ pwError }}</div>
      <div v-if="pwSuccess" class="mb-3 text-sm text-green-400">{{ pwSuccess }}</div>
      <div class="flex gap-3 justify-end">
        <button @click="showPwDialog = false" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
        <button @click="changePassword" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">確認修改</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from './Sidebar.vue'
import MobileTabBar from './MobileTabBar.vue'

const route = useRoute()
const router = useRouter()
const userName = ref('...')
const userId = ref('')
const userRole = ref('viewer')
const menuOpen = ref(false)
const drawerOpen = ref(false)
const showPwDialog = ref(false)
const pwForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const pwError = ref('')
const pwSuccess = ref('')
const groups = ref([
  { id: 'bikini-bottom', display: '比奇堡', icon: '🏝️' },
  { id: 'keding-dc', display: '科定DC', icon: '🏢' },
  { id: 'keding-wecom', display: '科定WeCom', icon: '💬' },
])
const currentGroup = ref(new URLSearchParams(window.location.search).get('group') || localStorage.getItem('adminGroup') || 'bikini-bottom')
const currentGroupDisplay = computed(() => groups.value.find(g => g.id === currentGroup.value)?.display || currentGroup.value)

const DC_ONLY_PATHS = ['/members', '/threads', '/thread-analytics', '/messaging']

function onGroupChange() {
  localStorage.setItem('adminGroup', currentGroup.value)
  const url = new URL(window.location)
  url.searchParams.set('group', currentGroup.value)
  history.replaceState(null, '', url)
  if (currentGroup.value === 'keding-wecom' && DC_ONLY_PATHS.includes(route.path)) {
    router.push('/')
  }
  window.dispatchEvent(new CustomEvent('group-changed', { detail: currentGroup.value }))
}

provide('currentGroup', currentGroup)
provide('onGroupChange', onGroupChange)

const pageTitle = computed(() => {
  const map = {
    home: '總覽', metrics: '資源監控', costs: '成本監控', alerts: '異常通知',
    messaging: '訊息推送', members: '成員管理', threads: '討論串管理', 'thread-analytics': '討論串分析',
    'agent-config': '角色配置', mcp: 'MCP 管理', 'mcp-servers': 'MCP 伺服器', skills: '技能管理', steering: '行為指引',
    cronjobs: '排程任務', knowledge: '知識庫',
    system: '系統資源', logs: '日誌搜尋', deploy: '部署管理', 'api-keys': 'API 金鑰',
    users: '使用者管理',
  }
  return map[route.name] || '總覽'
})

onMounted(async () => {
  try {
    const res = await fetch('/api/me')
    if (res.ok) {
      const data = await res.json()
      userName.value = data.name
      userId.value = data.id
      userRole.value = data.role || 'viewer'
    }
  } catch {}
  try {
    const res = await fetch('/api/groups')
    if (res.ok) {
      const data = await res.json()
      groups.value = data.groups || []
    }
  } catch {}
})

async function changePassword() {
  pwError.value = ''
  pwSuccess.value = ''
  if (!pwForm.oldPassword) { pwError.value = '請輸入舊密碼'; return }
  if (!pwForm.newPassword || pwForm.newPassword.length < 6) { pwError.value = '新密碼至少 6 字元'; return }
  if (pwForm.newPassword !== pwForm.confirmPassword) { pwError.value = '兩次密碼不一致'; return }
  try {
    const res = await fetch('/api/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_password: pwForm.oldPassword, new_password: pwForm.newPassword })
    })
    const data = await res.json()
    if (res.ok) {
      pwSuccess.value = '密碼已更新'
      pwForm.oldPassword = ''; pwForm.newPassword = ''; pwForm.confirmPassword = ''
      setTimeout(() => { showPwDialog.value = false; pwSuccess.value = '' }, 1500)
    } else {
      pwError.value = data.detail || '修改失敗'
    }
  } catch { pwError.value = '網路錯誤' }
}
</script>
