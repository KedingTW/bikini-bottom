<template>
  <div class="flex flex-col items-center justify-center py-32">
    <div class="text-6xl mb-6">🚧</div>
    <h2 class="text-2xl font-bold mb-2">{{ title }}</h2>
    <p class="text-white/50">功能開發中，敬請期待</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const titles = {
  messaging: '訊息推送',
  members: '成員管理',
  'thread-analytics': '討論串分析',
  'agent-config': '角色配置',
  cronjobs: '排程任務管理',
  knowledge: 'Knowledge Base',
  system: '系統資源',
  logs: 'Log 搜尋',
  deploy: '部署管理',
  'api-keys': 'API Key 管理',
}
const title = computed(() => titles[route.name] || '開發中')
</script>
