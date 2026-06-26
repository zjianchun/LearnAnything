<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const today = ref<any>(null)
const weekly = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  const [todayRes, weeklyRes] = await Promise.all([
    api.get('/stats/today'),
    api.get('/stats/weekly'),
  ])
  today.value = todayRes.data
  weekly.value = weeklyRes.data
  loading.value = false
})
</script>

<template>
  <div class="parent-dash">
    <h1>📊 家长看板</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <div class="today-card">
        <h2>今日学习</h2>
        <div class="stats-row">
          <div class="stat">
            <span class="stat-value">{{ (today?.math_minutes || 0) + (today?.physics_minutes || 0) + (today?.english_minutes || 0) }}</span>
            <span class="stat-label">学习分钟</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ today?.questions_total || 0 }}</span>
            <span class="stat-label">做题数</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ today?.questions_total ? Math.round((today.questions_correct / today.questions_total) * 100) : 0 }}%</span>
            <span class="stat-label">正确率</span>
          </div>
        </div>
      </div>

      <div class="subject-rates">
        <div class="rate-card">
          <h3>📐 数学</h3>
          <span class="rate">{{ today?.math_correct_rate ? Math.round(today.math_correct_rate * 100) : '--' }}%</span>
        </div>
        <div class="rate-card">
          <h3>🔬 物理</h3>
          <span class="rate">{{ today?.physics_correct_rate ? Math.round(today.physics_correct_rate * 100) : '--' }}%</span>
        </div>
        <div class="rate-card">
          <h3>🔤 英语</h3>
          <span class="rate">{{ today?.english_correct_rate ? Math.round(today.english_correct_rate * 100) : '--' }}%</span>
        </div>
      </div>

      <div class="weekly-section">
        <h2>近7天趋势</h2>
        <div v-if="weekly.length" class="weekly-list">
          <div v-for="day in weekly" :key="day.date" class="day-row">
            <span class="day-date">{{ day.date.slice(5) }}</span>
            <span class="day-bar">
              <span class="bar" :style="{ width: `${(day.questions_total || 0) * 3}px` }"></span>
            </span>
            <span class="day-count">{{ day.questions_total }}题</span>
            <span class="day-rate">{{ day.questions_total ? Math.round((day.questions_correct / day.questions_total) * 100) : 0 }}%</span>
          </div>
        </div>
        <p v-else class="empty">暂无数据</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.parent-dash h1 { margin-bottom: 1.5rem; }
.today-card {
  background: #fff; border-radius: 12px; padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.5rem;
}
.stats-row { display: flex; gap: 2rem; margin-top: 1rem; }
.stat { display: flex; flex-direction: column; align-items: center; }
.stat-value { font-size: 2rem; font-weight: 700; color: #4361ee; }
.stat-label { font-size: 0.8rem; color: #888; }
.subject-rates { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.rate-card {
  background: #fff; border-radius: 12px; padding: 1rem; text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.rate-card h3 { font-size: 0.9rem; margin-bottom: 0.5rem; }
.rate { font-size: 1.5rem; font-weight: 700; color: #333; }
.weekly-section { background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.weekly-section h2 { margin-bottom: 1rem; font-size: 1.1rem; }
.day-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.4rem 0; }
.day-date { width: 3rem; font-size: 0.85rem; color: #666; }
.bar { display: inline-block; height: 12px; background: #4361ee; border-radius: 6px; min-width: 4px; }
.day-count { font-size: 0.8rem; color: #666; width: 3rem; }
.day-rate { font-size: 0.8rem; color: #22c55e; }
.loading { text-align: center; padding: 3rem; color: #999; }
.empty { color: #aaa; }
</style>
