<template>
  <div class="p-4 sm:p-6">
    <div class="flex items-center gap-3 mb-5">
      <h2 class="text-lg font-semibold">約聘管理</h2>
      <div class="ml-auto flex gap-2">
        <router-link to="/contract/token-pool" class="text-xs px-3 py-1.5 rounded bg-ocean-700 border border-white/15 text-white/60 hover:text-white no-underline">🔑 帳號池</router-link>
        <button class="text-xs px-3 py-1.5 rounded bg-ocean-700 border border-white/15 text-white/30 cursor-not-allowed" disabled>🚀 開始約聘</button>
      </div>
    </div>

    <!-- 約聘名單 (主體) -->
    <div class="bg-ocean-800/50 rounded-lg border border-white/5 p-6 text-center">
      <div class="text-3xl mb-3">📋</div>
      <div class="text-sm text-white/50">目前尚無約聘人員</div>
    </div>
  </div>
</template>
