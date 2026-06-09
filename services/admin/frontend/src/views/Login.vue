<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="text-center mb-8">
        <img src="/header.png" alt="Logo" class="h-10 mx-auto mb-4">
        <h1 class="text-xl font-semibold">比奇堡團隊管理後台</h1>
        <p class="text-sm text-white/60 mt-1">請輸入員工編號登入</p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="bg-[rgba(15,25,45,0.85)] backdrop-blur-lg rounded-xl p-8 border border-white/10 shadow-2xl">
        <div v-if="error" class="mb-4 px-4 py-2.5 rounded-lg bg-red-500/20 text-red-300 text-sm text-center">{{ error }}</div>

        <div class="mb-5">
          <label class="block text-sm text-white/70 mb-1.5">員工編號</label>
          <input v-model="username" type="text" required autofocus
            class="w-full px-4 py-2.5 rounded-lg bg-[#0f1932] border border-white/20 text-white placeholder-white/40 focus:outline-none focus:border-cyan-400/60 transition"
            placeholder="例：11021395">
        </div>

        <div class="mb-6">
          <label class="block text-sm text-white/70 mb-1.5">密碼</label>
          <input v-model="password" type="password" required
            class="w-full px-4 py-2.5 rounded-lg bg-[#0f1932] border border-white/20 text-white placeholder-white/40 focus:outline-none focus:border-cyan-400/60 transition"
            placeholder="輸入密碼">
        </div>

        <button type="submit" :disabled="loading"
          class="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium transition">
          {{ loading ? '登入中...' : '登入' }}
        </button>
      </form>

      <!-- Footer -->
      <div class="mt-8 text-center">
        <img src="/footer.png" alt="Footer" class="h-8 mx-auto opacity-60">
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    })
    if (res.ok) {
      router.push('/')
    } else {
      const data = await res.json()
      error.value = data.detail || '登入失敗'
    }
  } catch {
    error.value = '網路連線錯誤'
  } finally {
    loading.value = false
  }
}
</script>
