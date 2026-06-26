<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const plan = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/plan/today')
    plan.value = data.plan
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="home">
    <h1>👋 今日学习计划</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="plan" class="plan-grid">
      <div v-for="(tasks, subject) in plan" :key="subject" class="subject-card">
        <h2>
          <span v-if="subject === 'math'">📐 数学</span>
          <span v-else-if="subject === 'physics'">🔬 物理</span>
          <span v-else>🔤 英语</span>
        </h2>
        <ul>
          <li v-for="task in tasks" :key="task.node_id" class="task-item">
            <span class="task-type" :class="task.type">
              {{ task.type === 'learn' ? '📖 新学' : task.type === 'review' ? '🔄 复习' : '✏️ 练习' }}
            </span>
            <router-link :to="task.type === 'practice' ? `/practice/${task.node_id}` : `/learn/${task.node_id}`">
              {{ task.name }}
            </router-link>
            <span class="task-time">{{ task.minutes }}分钟</span>
          </li>
        </ul>
        <p v-if="!tasks || tasks.length === 0" class="empty">暂无任务</p>
      </div>
    </div>

    <div class="quick-actions">
      <router-link to="/diagnosis" class="action-btn">🎯 学情诊断</router-link>
      <router-link to="/errors" class="action-btn">📝 错题复习</router-link>
      <router-link to="/progress" class="action-btn">📈 查看进度</router-link>
    </div>
  </div>
</template>

<style scoped>
.home h1 { margin-bottom: 1.5rem; }
.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
.subject-card {
  background: #fff;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.subject-card h2 { font-size: 1.1rem; margin-bottom: 0.75rem; }
.task-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}
.task-item a { color: #333; text-decoration: none; flex: 1; }
.task-item a:hover { color: #4361ee; }
.task-time { font-size: 0.8rem; color: #999; }
.task-type { font-size: 0.8rem; }
.quick-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}
.action-btn {
  padding: 0.75rem 1.5rem;
  background: #4361ee;
  color: #fff;
  border-radius: 8px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: transform 0.1s;
}
.action-btn:hover { transform: translateY(-2px); }
.loading { text-align: center; padding: 3rem; color: #999; }
.empty { color: #aaa; font-size: 0.9rem; }
</style>
