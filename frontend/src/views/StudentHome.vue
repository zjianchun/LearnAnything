<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const todayTasks = ref<any[]>([])
const stats = ref({ streak: 0, todayMinutes: 0, mastered: 0 })
const loading = ref(true)
const greeting = ref('')

onMounted(async () => {
  const hour = new Date().getHours()
  if (hour < 12) greeting.value = '早上好 ☀️'
  else if (hour < 18) greeting.value = '下午好 🌤️'
  else greeting.value = '晚上好 🌙'

  try {
    const [taskRes, statsRes] = await Promise.all([
      api.get('/tasks/today').catch(() => ({ data: [] })),
      api.get('/plan/today').catch(() => ({ data: { stats: null } })),
    ])
    todayTasks.value = taskRes.data
    if (statsRes.data?.stats) stats.value = statsRes.data.stats
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
    <!-- 顶部问候 -->
    <header class="hero">
      <div class="hero-text">
        <h1>{{ greeting }}</h1>
        <p class="subtitle">继续加油，每天进步一点点</p>
      </div>
      <div class="hero-avatar">🎯</div>
    </header>

    <!-- 今日数据卡 -->
    <div class="stats-row">
      <div class="stat-pill">
        <span class="stat-num tabular-nums">{{ stats.streak }}</span>
        <span class="stat-label">连续天</span>
      </div>
      <div class="stat-pill">
        <span class="stat-num tabular-nums">{{ stats.todayMinutes }}</span>
        <span class="stat-label">今日分钟</span>
      </div>
      <div class="stat-pill">
        <span class="stat-num tabular-nums">{{ stats.mastered }}</span>
        <span class="stat-label">已掌握</span>
      </div>
    </div>

    <!-- 今日任务 -->
    <section class="section">
      <h2 class="section-title">今日任务</h2>

      <div v-if="loading" class="skeleton-list">
        <div class="skeleton-item" v-for="i in 3" :key="i"></div>
      </div>

      <div v-else-if="todayTasks.length === 0" class="empty-card">
        <span class="empty-icon">🎉</span>
        <p>今日任务全部完成！</p>
        <p class="empty-hint">去自由练习巩固一下吧</p>
      </div>

      <div v-else class="task-list">
        <div v-for="t in todayTasks" :key="t.id" class="task-card" :class="{ overdue: t.overdue }">
          <div class="task-left">
            <span class="task-type-badge" :class="t.type">
              {{ t.type === 'practice' ? '✏️' : t.type === 'memory' ? '🧠' : t.type === 'courseware' ? '📖' : '📋' }}
            </span>
            <div class="task-info">
              <span class="task-title">{{ t.title }}</span>
              <span class="task-meta">{{ t.note || '完成即可' }}</span>
            </div>
          </div>
          <button v-if="t.type==='custom'" @click="completeTask(t.id)" class="task-action done">完成</button>
          <router-link v-else-if="t.type==='practice' && t.node_id" :to="`/practice/${t.node_id}`" class="task-action go">做题</router-link>
          <router-link v-else-if="t.type==='memory'" to="/memory" class="task-action go">背诵</router-link>
          <router-link v-else-if="t.type==='courseware' && t.node_id" :to="`/learn/${t.node_id}`" class="task-action go">学习</router-link>
          <button v-else @click="completeTask(t.id)" class="task-action done">完成</button>
        </div>
      </div>
    </section>

    <!-- 快捷入口 -->
    <section class="section">
      <h2 class="section-title">快捷入口</h2>
      <div class="quick-grid">
        <router-link to="/diagnosis" class="quick-item">
          <span class="quick-icon">🎯</span>
          <span class="quick-label">学情诊断</span>
        </router-link>
        <router-link to="/errors" class="quick-item">
          <span class="quick-icon">📝</span>
          <span class="quick-label">错题复习</span>
        </router-link>
        <router-link to="/library" class="quick-item">
          <span class="quick-icon">📖</span>
          <span class="quick-label">课件库</span>
        </router-link>
        <router-link to="/path" class="quick-item">
          <span class="quick-icon">🗺️</span>
          <span class="quick-label">学习路径</span>
        </router-link>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  padding-top: 0.5rem;
}

/* Hero */
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
.hero h1 {
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-text);
}
.subtitle {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  margin-top: 0.2rem;
}
.hero-avatar {
  width: 48px;
  height: 48px;
  background: var(--color-primary-bg);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

/* Stats */
.stats-row {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
}
.stat-pill {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.8rem 0.5rem;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
.stat-num {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1.2;
}
.stat-label {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  margin-top: 0.2rem;
}

/* Sections */
.section {
  margin-bottom: 2rem;
}
.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.75rem;
}

/* Task List */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.task-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1rem;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: transform 0.15s ease;
}
.task-card:active {
  transform: scale(0.98);
}
.task-card.overdue {
  border-left: 3px solid var(--color-danger);
}
.task-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.task-type-badge {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 1.1rem;
  background: var(--color-primary-bg);
}
.task-info {
  display: flex;
  flex-direction: column;
}
.task-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text);
}
.task-meta {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  margin-top: 0.1rem;
}
.task-action {
  padding: 0.4rem 0.9rem;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}
.task-action.go {
  background: var(--color-primary);
  color: #fff;
}
.task-action.go:hover {
  background: #5a4bd6;
}
.task-action.done {
  background: var(--color-accent);
  color: #fff;
}

/* Empty */
.empty-card {
  text-align: center;
  padding: 2rem 1rem;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
.empty-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.5rem;
}
.empty-card p {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text);
}
.empty-hint {
  font-size: 0.8rem !important;
  color: var(--color-text-muted) !important;
  font-weight: 400 !important;
  margin-top: 0.3rem;
}

/* Skeleton */
.skeleton-list { display: flex; flex-direction: column; gap: 0.6rem; }
.skeleton-item {
  height: 60px;
  background: linear-gradient(90deg, #f0f0f3 25%, #e8e8eb 50%, #f0f0f3 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-md);
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* Quick Grid */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}
.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 1rem 0.5rem;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  text-decoration: none;
  transition: transform 0.15s ease;
}
.quick-item:active {
  transform: scale(0.95);
}
.quick-icon {
  font-size: 1.5rem;
}
.quick-label {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}
</style>
