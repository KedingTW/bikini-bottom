import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Metrics from './views/Metrics.vue'
import Costs from './views/Costs.vue'
import Alerts from './views/Alerts.vue'
import Messaging from './views/Messaging.vue'
import Members from './views/Members.vue'
import Discord from './views/Discord.vue'
import ThreadAnalytics from './views/ThreadAnalytics.vue'
import Users from './views/Users.vue'
import ComingSoon from './views/ComingSoon.vue'

const routes = [
  { path: '/', name: 'home', component: Dashboard },
  { path: '/metrics', name: 'metrics', component: Metrics },
  { path: '/costs', name: 'costs', component: Costs },
  { path: '/alerts', name: 'alerts', component: Alerts },
  // 通訊管理
  { path: '/messaging', name: 'messaging', component: Messaging },
  { path: '/members', name: 'members', component: Members },
  { path: '/threads', name: 'threads', component: Discord },
  { path: '/thread-analytics', name: 'thread-analytics', component: ThreadAnalytics },
  // AI 角色管理
  { path: '/agent-config', name: 'agent-config', component: ComingSoon },
  { path: '/cronjobs', name: 'cronjobs', component: ComingSoon },
  { path: '/knowledge', name: 'knowledge', component: ComingSoon },
  // 系統運維
  { path: '/system', name: 'system', component: ComingSoon },
  { path: '/logs', name: 'logs', component: ComingSoon },
  { path: '/deploy', name: 'deploy', component: ComingSoon },
  { path: '/api-keys', name: 'api-keys', component: ComingSoon },
  // 系統管理
  { path: '/users', name: 'users', component: Users },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
