import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('../views/StudentHome.vue') },
  { path: '/learn/:nodeId', component: () => import('../views/Learn.vue') },
  { path: '/practice/:nodeId', component: () => import('../views/Practice.vue') },
  { path: '/diagnosis', component: () => import('../views/Diagnosis.vue') },
  { path: '/errors', component: () => import('../views/ErrorBook.vue') },
  { path: '/progress', component: () => import('../views/Progress.vue') },
  { path: '/parent', component: () => import('../views/ParentDash.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
