<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const errors = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  const { data } = await api.get('/stats/error-book')
  errors.value = data
  loading.value = false
})
</script>

<template>
  <div class="error-book">
    <h1>📝 错题本</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="errors.length === 0" class="empty-state">
      <p>🎉 还没有错题，继续保持！</p>
    </div>

    <div v-else class="error-list">
      <div v-for="err in errors" :key="err.question_id" class="error-card">
        <div class="error-header">
          <span class="node-name">{{ err.node_name }}</span>
          <span class="error-count">错{{ err.error_count }}次</span>
        </div>
        <p class="question-text">{{ err.question }}</p>
        <div class="error-footer">
          <span class="review-info">
            复习阶段：{{ ['新错题', '1天后', '3天后', '7天后'][err.review_stage] || '待复习' }}
          </span>
          <router-link :to="`/practice/${err.node_id}`" class="review-btn">去复习</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-book h1 { margin-bottom: 1.5rem; }
.error-list { display: flex; flex-direction: column; gap: 1rem; }
.error-card {
  background: #fff; border-radius: 12px; padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 4px solid #ef4444;
}
.error-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.node-name { font-weight: 600; color: #333; }
.error-count { font-size: 0.8rem; color: #ef4444; }
.question-text { color: #555; font-size: 0.95rem; line-height: 1.5; margin-bottom: 0.75rem; }
.error-footer { display: flex; justify-content: space-between; align-items: center; }
.review-info { font-size: 0.8rem; color: #888; }
.review-btn {
  padding: 0.4rem 1rem; background: #4361ee; color: #fff;
  border-radius: 6px; text-decoration: none; font-size: 0.85rem;
}
.empty-state { text-align: center; padding: 4rem; color: #888; }
.loading { text-align: center; padding: 3rem; color: #999; }
</style>
