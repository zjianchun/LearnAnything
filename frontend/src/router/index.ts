import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('../views/StudentHome.vue') },
  { path: '/graph', component: () => import('../views/SubjectGraph.vue') },
  { path: '/map', component: () => import('../views/KnowledgeMap.vue') },
  { path: '/map/:subject', component: () => import('../views/KnowledgeMap.vue') },
  { path: '/path', component: () => import('../views/LearningPath.vue') },
  { path: '/library', component: () => import('../views/CoursewareLib.vue') },
  { path: '/pbl', component: () => import('../views/PBL.vue') },
  { path: '/memory', component: () => import('../views/Memory.vue') },
  { path: '/learn/:nodeId', component: () => import('../views/Learn.vue') },
  { path: '/practice', component: () => import('../views/Practice.vue') },
  { path: '/practice/:nodeId', component: () => import('../views/Practice.vue') },
  { path: '/diagnosis', component: () => import('../views/Diagnosis.vue') },
  { path: '/errors', component: () => import('../views/ErrorBook.vue') },
  { path: '/progress', component: () => import('../views/Progress.vue') },
  { path: '/parent', component: () => import('../views/ParentDash.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
