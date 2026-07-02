<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const subjects = ref<any[]>([])
const loading = ref(true)
const overall = ref({ total: 0, mastered: 0, learning: 0 })

onMounted(async () => {
  const { data } = await api.get('/graph/subjects')
  subjects.value = data
  overall.value = {
    total: data.reduce((s: number, x: any) => s + x.total, 0),
    mastered: data.reduce((s: number, x: any) => s + x.mastered, 0),
    learning: data.reduce((s: number, x: any) => s + x.learning, 0),
  }
  loading.value = false
})

function pct(x: any) {
  return x.total ? Math.round((x.mastered / x.total) * 100) : 0
}
function masteryColor(m: number): string {
  if (m >= 0.8) return '#22c55e'
  if (m >= 0.5) return '#eab308'
  if (m > 0) return '#ef4444'
  return '#cbd5e1'
}
function openSubject(s: string) {
  router.push(`/map/${s}`)
}
</script>

<template>
  <div class="sgraph">
    <h1>🌐 全科图谱</h1>
    <p class="subtitle">初中9科知识结构总览 · 点学科进入知识地图</p>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <!-- 总体进度 -->
      <div class="overall">
        <div class="ov-item"><span class="ov-num">{{ subjects.length }}</span><span class="ov-label">学科</span></div>
        <div class="ov-item"><span class="ov-num">{{ overall.total }}</span><span class="ov-label">知识点</span></div>
        <div class="ov-item"><span class="ov-num green">{{ overall.mastered }}</span><span class="ov-label">已掌握</span></div>
        <div class="ov-item"><span class="ov-num yellow">{{ overall.learning }}</span><span class="ov-label">学习中</span></div>
      </div>

      <!-- 学科卡片网格 -->
      <div class="grid">
        <div v-for="s in subjects" :key="s.subject" class="card" @click="openSubject(s.subject)">
          <div class="card-head">
            <span class="icon">{{ s.icon }}</span>
            <span class="name">{{ s.name }}</span>
            <span class="count">{{ s.mastered }}/{{ s.total }}</span>
          </div>
          <div class="bar-bg">
            <div class="bar-fill" :style="{ width: pct(s) + '%' }"></div>
          </div>
          <div class="card-foot">
            <span class="dot-row">
              <i :style="{ background: masteryColor(s.avg_mastery) }"></i>
              平均掌握度 {{ Math.round(s.avg_mastery * 100) }}%
            </span>
            <span class="enter">进入 →</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.sgraph { padding-top: 0.5rem; }
.sgraph h1 { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 0.2rem; }
.subtitle { color: var(--text-3); font-size: 0.78rem; margin-bottom: 1.5rem; font-weight: 500; }

.overall {
  display: flex; justify-content: space-around;
  background: var(--surface); border-radius: var(--radius-lg); padding: 1.1rem 0.5rem;
  box-shadow: var(--shadow-sm); margin-bottom: 1.5rem;
}
.ov-item { display: flex; flex-direction: column; align-items: center; }
.ov-num { font-size: 1.4rem; font-weight: 800; color: var(--text-1); font-variant-numeric: tabular-nums; }
.ov-num.green { color: var(--success); }
.ov-num.yellow { color: var(--warning); }
.ov-label { font-size: 0.65rem; color: var(--text-3); margin-top: 0.1rem; font-weight: 500; }

.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; }

@media (max-width: 768px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}
.card {
  background: var(--surface); border-radius: var(--radius-md); padding: 1rem;
  box-shadow: var(--shadow-sm); cursor: pointer; transition: transform 0.5s var(--ease);
}
.card:active { transform: scale(0.96); }
.card-head { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.6rem; }
.icon { font-size: 1.2rem; }
.name { font-size: 0.85rem; font-weight: 700; color: var(--text-1); flex: 1; }
.count { font-size: 0.68rem; color: var(--text-3); font-variant-numeric: tabular-nums; }

.bar-bg { height: 5px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 0.5rem; }
.bar-fill { height: 100%; background: var(--accent); border-radius: 3px; transition: width 0.6s var(--ease); }

.card-foot { display: flex; justify-content: space-between; align-items: center; font-size: 0.68rem; color: var(--text-3); }
.dot-row { display: flex; align-items: center; gap: 0.25rem; }
.dot-row i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.enter { color: var(--accent); font-weight: 600; }

.loading { text-align: center; padding: 3rem; color: var(--text-3); }
</style>
