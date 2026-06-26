<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const projects = ref<any[]>([])
const loading = ref(true)
const interest = ref('')
const analyzing = ref(false)
const analyzeResult = ref<any>(null)

const SUBJECT_ICON: Record<string, string> = {
  math: '📐', physics: '⚡', chemistry: '🧪', english: '🔤', chinese: '📝',
  biology: '🌱', geography: '🗺️', history: '📜', politics: '⚖️',
}

onMounted(async () => {
  const { data } = await api.get('/pbl/list')
  projects.value = data.projects
  loading.value = false
})

async function analyze() {
  if (!interest.value.trim()) return
  analyzing.value = true
  analyzeResult.value = null
  try {
    const { data } = await api.post('/pbl/analyze', { interest: interest.value, stage: 'middle' })
    analyzeResult.value = data
  } catch (e: any) {
    analyzeResult.value = { error: e?.message || '请求失败' }
  } finally {
    analyzing.value = false
  }
}
</script>

<template>
  <div class="pbl">
    <h1>🔬 PBL 探究</h1>
    <p class="subtitle">用真实问题驱动学习：在解决问题中掌握知识</p>

    <!-- 兴趣探索 -->
    <div class="explore">
      <h3>💡 按兴趣找探究课题</h3>
      <div class="explore-row">
        <input v-model="interest" placeholder="输入你感兴趣的话题，如：手机套餐、篮球、奶茶店定价…"
          @keyup.enter="analyze" />
        <button @click="analyze" :disabled="analyzing || !interest.trim()">
          {{ analyzing ? '匹配中...' : '探索' }}
        </button>
      </div>
      <div v-if="analyzeResult" class="analyze-result">
        <p v-if="analyzeResult.error" class="err">暂时无法匹配（{{ analyzeResult.error }}）。可先看下方精选课题。</p>
        <pre v-else>{{ JSON.stringify(analyzeResult, null, 2).slice(0, 600) }}</pre>
      </div>
    </div>

    <!-- 精选探究课题 -->
    <h3 class="sec">📋 精选探究课题</h3>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else class="grid">
      <div v-for="p in projects" :key="p.course_id" class="card">
        <div class="c-icon">{{ SUBJECT_ICON[p.subject] || '📚' }}</div>
        <div class="c-body">
          <div class="c-name">{{ p.name }}</div>
          <div class="c-sub">{{ p.subject_name }} 探究</div>
        </div>
        <router-link v-if="p.self_hosted" :to="`/learn/${p.course_id}`" class="go">开始探究 →</router-link>
        <span v-else class="soon">可拉取</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pbl h1 { margin-bottom: 0.25rem; }
.subtitle { color: #94a3b8; font-size: 0.85rem; margin-bottom: 1.25rem; }
.explore { background: #fff; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.5rem; }
.explore h3 { margin-bottom: 0.75rem; }
.explore-row { display: flex; gap: 0.6rem; }
.explore-row input { flex: 1; padding: 0.6rem 0.9rem; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.9rem; }
.explore-row button { padding: 0.6rem 1.4rem; background: #4361ee; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9rem; }
.explore-row button:disabled { background: #cbd5e1; cursor: not-allowed; }
.analyze-result { margin-top: 0.75rem; }
.analyze-result .err { color: #b45309; font-size: 0.85rem; }
.analyze-result pre { background: #f8fafc; padding: 0.75rem; border-radius: 8px; font-size: 0.75rem; overflow-x: auto; }
.sec { margin-bottom: 0.75rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.85rem; }
.card { display: flex; align-items: center; gap: 0.75rem; background: #fff; border-radius: 12px; padding: 1rem 1.1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.c-icon { font-size: 1.8rem; }
.c-body { flex: 1; }
.c-name { font-weight: 600; color: #1e293b; font-size: 0.92rem; line-height: 1.3; }
.c-sub { font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem; }
.go { font-size: 0.82rem; color: #4361ee; text-decoration: none; white-space: nowrap; }
.soon { font-size: 0.75rem; color: #94a3b8; }
.loading { text-align: center; padding: 2rem; color: #94a3b8; }
</style>
