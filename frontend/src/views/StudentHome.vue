<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const todayTasks = ref<any[]>([])
const loading = ref(true)
const greeting = ref('')

onMounted(async () => {
  const hour = new Date().getHours()
  if (hour < 12) greeting.value = '早上好'
  else if (hour < 18) greeting.value = '下午好'
  else greeting.value = '晚上好'

  try {
    const res = await api.get('/tasks/today').catch(() => ({ data: [] }))
    todayTasks.value = res.data
  } finally {
    loading.value = false
  }
})

async function completeTask(id: number) {
  await api.post(`/tasks/${id}/complete`, { result: {} })
  todayTasks.value = todayTasks.value.filter(t => t.id !== id)
}
</script>

<template>
  <div class="home">
    <!-- Header -->
    <header class="header">
      <div>
        <p class="greeting">{{ greeting }}</p>
        <h1 class="title">今日学习</h1>
      </div>
    </header>

    <!-- 任务区 -->
    <section class="section">
      <div class="section-header">
        <h2>待完成</h2>
        <span v-if="todayTasks.length" class="badge">{{ todayTasks.length }}</span>
      </div>

      <div v-if="loading" class="skeleton-wrap">
        <div class="skeleton" v-for="i in 3" :key="i"></div>
      </div>

      <div v-else-if="todayTasks.length === 0" class="empty-state">
        <p class="empty-emoji">✨</p>
        <p class="empty-text">全部完成，今天很棒</p>
      </div>

      <div v-else class="task-list">
        <div v-for="t in todayTasks" :key="t.id" class="task-item">
          <div class="task-dot" :class="t.type"></div>
          <div class="task-body">
            <p class="task-title">{{ t.title }}</p>
            <p class="task-sub">{{ t.note || '完成即可' }}</p>
          </div>
          <router-link v-if="t.type==='practice' && t.node_id" :to="`/practice/${t.node_id}`" class="task-btn">开始</router-link>
          <router-link v-else-if="t.type==='memory'" to="/memory" class="task-btn">开始</router-link>
          <router-link v-else-if="t.type==='courseware' && t.node_id" :to="`/learn/${t.node_id}`" class="task-btn">开始</router-link>
          <button v-else @click="completeTask(t.id)" class="task-btn done">完成</button>
        </div>
      </div>
    </section>

    <!-- 快捷入口 -->
    <section class="section">
      <h2 class="section-header">快捷入口</h2>
      <div class="quick-row">
        <router-link to="/diagnosis" class="quick-card">
          <span class="qc-icon">🎯</span>
          <span class="qc-label">学情诊断</span>
        </router-link>
        <router-link to="/errors" class="quick-card">
          <span class="qc-icon">📝</span>
          <span class="qc-label">错题复习</span>
        </router-link>
        <router-link to="/library" class="quick-card">
          <span class="qc-icon">📖</span>
          <span class="qc-label">课件库</span>
        </router-link>
        <router-link to="/path" class="quick-card">
          <span class="qc-icon">🗺️</span>
          <span class="qc-label">学习路径</span>
        </router-link>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home { padding-top: 0.75rem; }

/* Header */
.header { margin-bottom: 2rem; }
.greeting {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-3);
  letter-spacing: 0.02em;
  margin-bottom: 0.15rem;
}
.title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-1);
  letter-spacing: -0.03em;
}

/* Section */
.section { margin-bottom: 2.25rem; }
.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.section-header h2 {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-2);
}
.badge {
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
}

/* Tasks */
.task-list { display: flex; flex-direction: column; gap: 0.5rem; }
.task-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.1rem;
  background: var(--surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: transform 0.5s var(--ease), box-shadow 0.5s var(--ease);
}
.task-item:active { transform: scale(0.985); }
.task-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  background: var(--accent);
}
.task-dot.memory { background: var(--success); }
.task-dot.courseware { background: var(--warning); }
.task-body { flex: 1; min-width: 0; }
.task-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-sub {
  font-size: 0.7rem;
  color: var(--text-3);
  margin-top: 0.1rem;
}
.task-btn {
  padding: 0.4rem 0.9rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: transform 0.3s var(--ease);
  white-space: nowrap;
}
.task-btn:active { transform: scale(0.92); }
.task-btn.done { background: var(--success); }

/* Empty */
.empty-state {
  text-align: center;
  padding: 2.5rem 1rem;
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
.empty-emoji { font-size: 2rem; margin-bottom: 0.4rem; }
.empty-text { font-size: 0.88rem; color: var(--text-3); font-weight: 500; }

/* Skeleton */
.skeleton-wrap { display: flex; flex-direction: column; gap: 0.5rem; }
.skeleton {
  height: 64px;
  border-radius: var(--radius-md);
  background: linear-gradient(90deg, var(--border) 25%, #E8E8ED 50%, var(--border) 75%);
  background-size: 200% 100%;
  animation: pulse 1.8s ease infinite;
}
@keyframes pulse { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* Quick Row */
.quick-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.6rem;
}
.quick-card {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 1rem 1.1rem;
  background: var(--surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  text-decoration: none;
  transition: transform 0.5s var(--ease), box-shadow 0.5s var(--ease);
}
.quick-card:active {
  transform: scale(0.97);
  box-shadow: var(--shadow-xs);
}
.qc-icon { font-size: 1.4rem; }
.qc-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-2);
}
</style>
