<template>
  <div class="glass px-7 py-3 flex items-center gap-5 border-b border-white/10 text-sm sticky top-0 z-10">
    <span class="font-medium">使用者管理</span>
    <button @click="showAdd = true" class="ml-auto bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1.5 rounded text-xs font-medium transition">+ 新增使用者</button>
  </div>

  <div class="p-7">
    <div class="glass rounded-xl overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="bg-ocean-800/60">
            <th class="text-left px-5 py-3 text-sm font-semibold">員工編號</th>
            <th class="text-left px-5 py-3 text-sm font-semibold">姓名</th>
            <th class="text-left px-5 py-3 text-sm font-semibold">部門</th>
            <th class="text-left px-5 py-3 text-sm font-semibold">角色</th>
            <th class="text-left px-5 py-3 text-sm font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-t border-white/5 hover:bg-white/5">
            <td class="px-5 py-3 text-sm">{{ u.id }}</td>
            <td class="px-5 py-3 text-sm font-medium">{{ u.name }}</td>
            <td class="px-5 py-3 text-sm text-white/70">{{ u.department }}</td>
            <td class="px-5 py-3 text-sm">
              <select :value="u.role" @change="changeRole(u.id, $event.target.value)"
                class="bg-ocean-800 text-white border border-white/20 rounded px-2 py-1 text-xs">
                <option value="admin">管理員</option>
                <option value="viewer">檢視者</option>
              </select>
            </td>
            <td class="px-5 py-3 text-sm">
              <div class="flex gap-2">
                <button @click="resetPw(u)" class="px-2 py-1 text-xs rounded border border-white/20 hover:bg-white/10 transition">🔑 重設密碼</button>
                <button @click="deleteUser(u)" class="px-2 py-1 text-xs rounded border border-red-400/30 text-red-300 hover:bg-red-400/10 transition">🗑️ 刪除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Add User Dialog -->
  <div v-if="showAdd" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" @click.self="showAdd = false">
    <div class="bg-ocean-700 rounded-xl w-full max-w-md p-6 shadow-2xl border border-white/10">
      <h3 class="text-lg font-semibold mb-4">新增使用者</h3>
      <div class="mb-3">
        <label class="block text-sm text-white/70 mb-1">員工編號</label>
        <input v-model="form.id" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white focus:outline-none focus:border-cyan-400/60">
      </div>
      <div class="mb-3">
        <label class="block text-sm text-white/70 mb-1">姓名</label>
        <input v-model="form.name" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white focus:outline-none focus:border-cyan-400/60">
      </div>
      <div class="mb-3">
        <label class="block text-sm text-white/70 mb-1">部門</label>
        <input v-model="form.department" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white focus:outline-none focus:border-cyan-400/60">
      </div>
      <div class="mb-3">
        <label class="block text-sm text-white/70 mb-1">角色</label>
        <select v-model="form.role" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white">
          <option value="admin">管理員</option>
          <option value="viewer">檢視者</option>
        </select>
      </div>
      <div class="mb-4">
        <label class="block text-sm text-white/70 mb-1">初始密碼</label>
        <input v-model="form.password" class="w-full px-3 py-2 rounded-lg bg-ocean-800 border border-white/20 text-white focus:outline-none focus:border-cyan-400/60" placeholder="預設：kd-22963999">
      </div>
      <div v-if="formError" class="mb-3 text-sm text-red-400">{{ formError }}</div>
      <div class="flex gap-3 justify-end">
        <button @click="showAdd = false" class="px-4 py-2 text-sm rounded-lg border border-white/20 text-white/70 hover:bg-white/10">取消</button>
        <button @click="createUser" class="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">新增</button>
      </div>
    </div>
  </div>

  <!-- Toast -->
  <div v-if="toast" class="fixed bottom-6 right-6 px-5 py-3 rounded-lg text-sm z-50 shadow-lg"
    :class="toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'">{{ toast.msg }}</div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useApi } from '../composables/useApi.js'

const { get, post } = useApi()

const users = ref([])
const showAdd = ref(false)
const formError = ref('')
const toast = ref(null)
const form = reactive({ id: '', name: '', department: '', role: 'viewer', password: '' })

async function load() {
  const data = await get('/api/users')
  users.value = data?.users || []
}

async function createUser() {
  formError.value = ''
  if (!form.id || !form.name) { formError.value = '員工編號和姓名為必填'; return }
  const res = await fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...form, password: form.password || 'kd-22963999' })
  })
  const data = await res.json()
  if (res.ok) {
    showAdd.value = false
    form.id = ''; form.name = ''; form.department = ''; form.role = 'viewer'; form.password = ''
    showToast('✅ 已新增', 'success')
    load()
  } else {
    formError.value = data.detail || '新增失敗'
  }
}

async function changeRole(userId, newRole) {
  await fetch(`/api/users/${userId}/role`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role: newRole })
  })
  showToast('✅ 角色已更新', 'success')
  load()
}

async function resetPw(u) {
  if (!confirm(`確定要重設 ${u.name} 的密碼為預設值？`)) return
  await post(`/api/users/${u.id}/reset-password`)
  showToast('✅ 密碼已重設', 'success')
}

async function deleteUser(u) {
  if (!confirm(`確定要刪除 ${u.name}？此操作無法恢復。`)) return
  const res = await fetch(`/api/users/${u.id}`, { method: 'DELETE' })
  const data = await res.json()
  if (res.ok) { showToast('✅ 已刪除', 'success'); load() }
  else showToast(`❌ ${data.detail}`, 'error')
}

function showToast(msg, type) {
  toast.value = { msg, type }
  setTimeout(() => { toast.value = null }, 3000)
}

onMounted(load)
</script>
