<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const plan = ref<any>(null)
const loading = ref(true)
const error = ref(false)
const todayTasks = ref<any[]>([])

onMounted(async () => {
  try {
    const [planRes, taskRes] = await Promise.all([
      api.get('/plan/today').catch(() => ({ data: { plan: null } })),
      api.get('/tasks/today').catch(() => ({ data: [] })),
    ])
    plan.value = planRes.data.plan
    todayTasks.value = taskRes.data
  } catch {
    error.value = true
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
    <h1>👋 今日学习计划</h1>

    <!-- 家长布置的任务 -->
    <div v-if="todayTasks.length" class="parent-tasks">
      <h3>📋 今日任务</h3>
      <div v-for="t in todayTasks" :key="t.id" class="ptask" :class="{ overdue: t.overdue }">
        <div class="ptask-info">
          <span class="ptask-title">{{ t.title }}</span>
          <span class="ptask-meta">{{ t.note || '' }} · 截止 {{ t.deadline }}</span>
        </div>
        <button v-if="t.type==='custom'" @click="completeTask(t.id)" class="ptask-btn">✓ 完成</button>
        <router-link v-else-if="t.type==='practice' && t.node_id" :to="`/practice/${t.node_id}`" class="ptask-btn">去做题</router-link>
        <router-link v-else-if="t.type==='memory'" to="/memory" class="ptask-btn">去背诵</router-link>
        <router-link v-else-if="t.type==='courseware' && t.node_id" :to="`/learn/${t.node_id}`" class="ptask-btn">去学习</router-link>
        <button v-else @click="completeTask(t.id)" class="ptask-btn">✓ 完成</button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="error || !plan" class="empty-state">
      <p>📋 暂无今日计划</p>
      <p class="hint">完成入学诊断后，系统将自动生成学习计划</p>
    </div>

    <div v-else class="plan-grid">
      <div v-for="(tasks, subject) in plan" :key="subject" class="subject-card">
        <h2>
          <span v-if="subject === 'math'">📐 数学</span>
          <span v-else-if="subject === 'physics'">🔬 物理</span>
          <span v-else>🔤 英语</span>
        </h2>
        <ul>
          <li v-for="task in tasks" :key="task.node_id" class="task-item">
            <span class="task-type">
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
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem; margin-bottom: 2rem;
}
.subject-card {
  background: #fff; border-radius: 12px; padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.subject-card h2 { font-size: 1.1rem; margin-bottom: 0.75rem; }
.task-item {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0;
}
.task-item a { color: #333; text-decoration: none; flex: 1; }
.task-item a:hover { color: #4361ee; }
.task-time { font-size: 0.8rem; color: #999; }
.task-type { font-size: 0.8rem; }
.quick-actions { display: flex; gap: 1rem; flex-wrap: wrap; }
.action-btn {
  padding: 0.75rem 1.5rem; background: #4361ee; color: #fff;
  border-radius: 8px; text-decoration: none; font-size: 0.9rem; transition: transform 0.1s;
}
.action-btn:hover { transform: translateY(-2px); }
.loading { text-align: center; padding: 3rem; color: #999; }
.empty { color: #aaa; font-size: 0.9rem; }
.empty-state { text-align: center; padding: 3rem; margin-bottom: 2rem; background: #fff; border-radius: 12px; }
.empty-state p { font-size: 1.2rem; margin-bottom: 0.5rem; }
.hint { font-size: 0.9rem; color: #888; }
.parent-tasks { background: #fff; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.5rem; }
.parent-tasks h3 { margin-bottom: 0.75rem; font-size: 1rem; }
.ptask { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid #f1f5f9; }
.ptask:last-child { border-bottom: none; }
.ptask.overdue { background: #fef2f2; margin: 0 -0.5rem; padding: 0.6rem 0.5rem; border-radius: 6px; border-bottom: none; }
.ptask-title { font-weight: 500; color: #1e293b; font-size: 0.9rem; }
.ptask-meta { display: block; font-size: 0.72rem; color: #94a3b8; }
.ptask.overdue .ptask-title::after { content: ' ⚠️过期'; color: #dc2626; font-size: 0.75rem; }
.ptask-btn { padding: 0.35rem 0.8rem; background: #4361ee; color: #fff; border: none; border-radius: 6px; font-size: 0.8rem; cursor: pointer; text-decoration: none; }
</style>
