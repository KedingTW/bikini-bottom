<template>
  <div class="p-4 sm:p-6">
    <h2 class="text-lg font-semibold mb-2">約聘管理</h2>
    <p class="text-sm text-white/50 mb-6">管理約聘角色的帳號與部署</p>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <router-link to="/contract/token-pool" class="bg-ocean-800/50 rounded-lg border border-white/5 p-5 hover:border-cyan-400/20 transition no-underline block">
        <div class="text-2xl mb-2">🔑</div>
        <div class="text-sm font-medium text-cyan-300 mb-1">帳號池</div>
        <div class="text-xs text-white/50">管理 Bot Token，分配帳號給約聘角色</div>
      </router-link>

      <div class="bg-ocean-800/50 rounded-lg border border-white/5 p-5 opacity-40 cursor-not-allowed">
        <div class="text-2xl mb-2">📋</div>
        <div class="text-sm font-medium text-white/60 mb-1">約聘名單</div>
        <div class="text-xs text-white/40">Coming soon</div>
      </div>

      <div class="bg-ocean-800/50 rounded-lg border border-white/5 p-5 opacity-40 cursor-not-allowed">
        <div class="text-2xl mb-2">🚀</div>
        <div class="text-sm font-medium text-white/60 mb-1">開始約聘</div>
        <div class="text-xs text-white/40">Coming soon</div>
      </div>
    </div>
  </div>
</template>
