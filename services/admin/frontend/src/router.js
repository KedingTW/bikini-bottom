import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Metrics from './views/Metrics.vue'
import Costs from './views/Costs.vue'
import Alerts from './views/Alerts.vue'
import Messaging from './views/Messaging.vue'
import Members from './views/Members.vue'
import Discord from './views/Discord.vue'
import ThreadAnalytics from './views/ThreadAnalytics.vue'
import AgentConfig from './views/AgentConfig.vue'
import McpManage from './views/McpManage.vue'
import McpServers from './views/McpServers.vue'
import SkillManage from './views/SkillManage.vue'
import SteeringManage from './views/SteeringManage.vue'
import Users from './views/Users.vue'
import ComingSoon from './views/ComingSoon.vue'
import Deploy from './views/Deploy.vue'
import Logs from './views/Logs.vue'
import Login from './views/Login.vue'

const routes = [
  { path: '/login', name: 'login', component: Login, meta: { public: true } },
  { path: '/', name: 'home', component: Dashboard },
  { path: '/metrics', name: 'metrics', component: Metrics },
  { path: '/costs', name: 'costs', component: Costs },
  { path: '/alerts', name: 'alerts', component: Alerts },
  // 通訊管理
  { path: '/members', name: 'members', component: Members },
  { path: '/threads', name: 'threads', component: Discord },
  { path: '/thread-analytics', name: 'thread-analytics', component: ThreadAnalytics },
  { path: '/messaging', name: 'messaging', component: Messaging },
  // AI 角色管理
  { path: '/agent-config', name: 'agent-config', component: AgentConfig },
  { path: '/mcp', name: 'mcp', component: McpManage },
  { path: '/mcp-servers', name: 'mcp-servers', component: McpServers },
  { path: '/skills', name: 'skills', component: SkillManage },
  { path: '/steering', name: 'steering', component: SteeringManage },
  { path: '/cronjobs', name: 'cronjobs', component: ComingSoon },
  { path: '/knowledge', name: 'knowledge', component: ComingSoon },
  // 系統運維
  { path: '/system', name: 'system', component: ComingSoon },
  { path: '/logs', name: 'logs', component: Logs },
  { path: '/deploy', name: 'deploy', component: Deploy },
  { path: '/api-keys', name: 'api-keys', component: ComingSoon },
  // 系統管理
  { path: '/users', name: 'users', component: Users },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  try {
    const res = await fetch('/api/me')
    if (res.ok) return true
  } catch {}
  return { name: 'login' }
})

export default router
