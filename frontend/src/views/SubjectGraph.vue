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
.sgraph h1 { margin-bottom: 0.25rem; }
.subtitle { color: #94a3b8; font-size: 0.85rem; margin-bottom: 1.5rem; }
.overall {
  display: flex; gap: 2rem; background: #fff; border-radius: 12px; padding: 1.25rem 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.5rem;
}
.ov-item { display: flex; flex-direction: column; align-items: center; }
.ov-num { font-size: 1.8rem; font-weight: 700; color: #1e293b; }
.ov-num.green { color: #22c55e; }
.ov-num.yellow { color: #eab308; }
.ov-label { font-size: 0.8rem; color: #94a3b8; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1rem; }
.card {
  background: #fff; border-radius: 12px; padding: 1.1rem 1.25rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); cursor: pointer; transition: transform 0.1s, box-shadow 0.1s;
}
.card:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.1); }
.card-head { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.icon { font-size: 1.5rem; }
.name { font-size: 1.05rem; font-weight: 700; color: #1e293b; flex: 1; }
.count { font-size: 0.8rem; color: #94a3b8; }
.bar-bg { height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; margin-bottom: 0.6rem; }
.bar-fill { height: 100%; background: linear-gradient(90deg, #4361ee, #22c55e); border-radius: 4px; transition: width 0.4s; }
.card-foot { display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: #64748b; }
.dot-row { display: flex; align-items: center; gap: 0.35rem; }
.dot-row i { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.enter { color: #4361ee; }
.loading { text-align: center; padding: 3rem; color: #94a3b8; }
</style>
