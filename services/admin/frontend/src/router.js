import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Metrics from './views/Metrics.vue'
import Alerts from './views/Alerts.vue'
import Users from './views/Users.vue'
import Costs from './views/Costs.vue'
import Discord from './views/Discord.vue'

const routes = [
  { path: '/', name: 'home', component: Dashboard },
  { path: '/metrics', name: 'metrics', component: Metrics },
  { path: '/alerts', name: 'alerts', component: Alerts },
  { path: '/users', name: 'users', component: Users },
  { path: '/costs', name: 'costs', component: Costs },
  { path: '/discord', name: 'discord', component: Discord },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
