<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const overview = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  const { data } = await api.get('/diagnosis/overview')
  overview.value = data
  loading.value = false
})

function statusColor(mastery: number): string {
  if (mastery >= 0.8) return '#22c55e'
  if (mastery >= 0.5) return '#eab308'
  if (mastery > 0) return '#ef4444'
  return '#d1d5db'
}
</script>

<template>
  <div class="diagnosis">
    <h1>🎯 学情诊断</h1>
    <p class="subtitle">绿色=掌握 · 黄色=半会 · 红色=薄弱 · 灰色=未学</p>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="subjects">
      <div v-for="(nodes, subject) in overview" :key="subject" class="subject-section">
        <h2>
          <span v-if="subject === 'math'">📐 数学</span>
          <span v-else-if="subject === 'physics'">🔬 物理</span>
          <span v-else>🔤 英语</span>
        </h2>
        <div class="node-grid">
          <router-link
            v-for="node in nodes" :key="node.node_id"
            :to="`/practice/${node.node_id}`"
            class="node-chip"
            :style="{ borderColor: statusColor(node.mastery) }"
          >
            <span class="dot" :style="{ background: statusColor(node.mastery) }"></span>
            {{ node.name }}
            <span class="pct">{{ Math.round(node.mastery * 100) }}%</span>
          </router-link>
        </div>
        <p v-if="!nodes?.length" class="empty">暂无数据，请先完成入学诊断</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.diagnosis h1 { margin-bottom: 0.25rem; }
.subtitle { color: #888; font-size: 0.85rem; margin-bottom: 1.5rem; }
.subject-section { margin-bottom: 2rem; }
.subject-section h2 { margin-bottom: 0.75rem; }
.node-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.node-chip {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.4rem 0.8rem; border: 2px solid; border-radius: 20px;
  font-size: 0.85rem; text-decoration: none; color: #333; background: #fff;
  transition: transform 0.1s;
}
.node-chip:hover { transform: scale(1.05); }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.pct { font-size: 0.75rem; color: #999; }
.loading { text-align: center; padding: 3rem; color: #999; }
.empty { color: #aaa; }
</style>
