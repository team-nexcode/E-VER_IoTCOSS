import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout/Layout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Layout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/pages/Dashboard.vue'),
        },
        {
          path: 'devices',
          name: 'devices',
          component: () => import('@/pages/Devices.vue'),
        },
        {
          path: 'power',
          name: 'power',
          component: () => import('@/pages/PowerAnalysis.vue'),
        },
        {
          path: 'schedule',
          name: 'schedule',
          component: () => import('@/pages/Schedule.vue'),
        },
        {
          path: 'alerts',
          name: 'alerts',
          component: () => import('@/pages/Alerts.vue'),
        },
        {
          path: 'system-log',
          name: 'system-log',
          component: () => import('@/pages/SystemLog.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/pages/Settings.vue'),
        },
      ],
    },
  ],
})

export default router
