<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const masteryMap = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  const { data } = await api.get('/stats/mastery-map')
  masteryMap.value = data
  loading.value = false
})

function masteryBar(m: number) {
  return { width: `${m * 100}%` }
}
function masteryColor(m: number) {
  if (m >= 0.8) return '#22c55e'
  if (m >= 0.5) return '#eab308'
  if (m > 0) return '#ef4444'
  return '#d1d5db'
}
</script>

<template>
  <div class="progress">
    <h1>📈 学习进度</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else>
      <div v-for="(nodes, subject) in masteryMap" :key="subject" class="subject-section">
        <h2>
          <span v-if="subject === 'math'">📐 数学</span>
          <span v-else-if="subject === 'physics'">🔬 物理</span>
          <span v-else>🔤 英语</span>
          <span class="count">({{ nodes.filter((n: any) => n.mastery >= 0.8).length }}/{{ nodes.length }} 掌握)</span>
        </h2>
        <div class="node-list">
          <div v-for="node in nodes" :key="node.node_id" class="node-row">
            <span class="node-name">{{ node.name }}</span>
            <div class="bar-bg">
              <div class="bar-fill" :style="{ ...masteryBar(node.mastery), background: masteryColor(node.mastery) }"></div>
            </div>
            <span class="pct">{{ Math.round(node.mastery * 100) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.progress h1 { margin-bottom: 1.5rem; }
.subject-section { margin-bottom: 2rem; }
.subject-section h2 { margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }
.count { font-size: 0.8rem; color: #888; font-weight: 400; }
.node-list { background: #fff; border-radius: 12px; padding: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.node-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid #f5f5f5; }
.node-row:last-child { border-bottom: none; }
.node-name { width: 140px; font-size: 0.9rem; color: #333; flex-shrink: 0; }
.bar-bg { flex: 1; height: 10px; background: #f0f0f0; border-radius: 5px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 5px; transition: width 0.3s; }
.pct { width: 3rem; text-align: right; font-size: 0.8rem; color: #666; }
.loading { text-align: center; padding: 3rem; color: #999; }
</style>
