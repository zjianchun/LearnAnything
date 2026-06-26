<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import api from '../api'

const subjects = ref<any[]>([])
const subject = ref('math')
const data = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  const { data: subs } = await api.get('/graph/subjects')
  subjects.value = subs
  await load()
})
watch(subject, load)

async function load() {
  loading.value = true
  const { data: d } = await api.get(`/graph/path/${subject.value}`)
  data.value = d
  loading.value = false
}

const stateInfo: Record<string, { label: string; color: string; icon: string }> = {
  mastered: { label: '已掌握', color: '#22c55e', icon: '✓' },
  learning: { label: '学习中', color: '#eab308', icon: '◐' },
  ready: { label: '可学', color: '#4361ee', icon: '▶' },
  locked: { label: '未解锁', color: '#cbd5e1', icon: '🔒' },
}

function gradeLabel(g: number): string {
  const m: Record<number, string> = { 7: '初一', 8: '初二', 9: '初三' }
  return m[g] || `${g}年级`
}
</script>

<template>
  <div class="path">
    <h1>🧭 学习路径</h1>
    <p class="subtitle">按知识依赖 + 你的掌握度 + 中考考频，为你规划学习顺序</p>

    <div class="subject-tabs">
      <button v-for="s in subjects" :key="s.subject" class="tab"
        :class="{ active: s.subject === subject }" @click="subject = s.subject">
        {{ s.icon }} {{ s.name }}
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else-if="data">
      <!-- 下一步推荐 -->
      <div class="next-up" v-if="data.next_up.length">
        <h3>🎯 接下来学这些</h3>
        <div class="next-cards">
          <div v-for="n in data.next_up" :key="n.node_id" class="next-card"
            :style="{ borderTopColor: stateInfo[n.state].color }">
            <div class="nc-head">
              <span class="nc-name">{{ n.name }}</span>
              <span v-if="n.exam_weight === 'high'" class="hot">★高频</span>
            </div>
            <div class="nc-chapter">{{ n.chapter }}</div>
            <div class="nc-actions">
              <router-link :to="`/learn/${n.node_id}`" class="mini-btn">学</router-link>
              <router-link :to="`/practice/${n.node_id}`" class="mini-btn ghost">练</router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- 进度统计 -->
      <div class="stats">
        <span v-for="(info, key) in stateInfo" :key="key" class="stat">
          <i :style="{ background: info.color }"></i>{{ info.label }} {{ data.stats[key] }}
        </span>
      </div>

      <!-- 完整路径时间线 -->
      <div class="timeline">
        <div v-for="n in data.path" :key="n.node_id" class="tl-item" :class="n.state">
          <span class="tl-dot" :style="{ background: stateInfo[n.state].color }">{{ stateInfo[n.state].icon }}</span>
          <div class="tl-body">
            <div class="tl-row">
              <span class="tl-name">{{ n.name }}</span>
              <span class="tl-grade">{{ gradeLabel(n.grade) }}</span>
              <span v-if="n.exam_weight === 'high'" class="hot">★</span>
              <span class="tl-state" :style="{ color: stateInfo[n.state].color }">{{ stateInfo[n.state].label }}</span>
            </div>
            <div class="tl-sub">
              {{ n.chapter }}
              <span v-if="n.state === 'locked' && n.blocked_by.length" class="blocked">· 需先掌握前置</span>
            </div>
          </div>
          <div class="tl-actions" v-if="n.state !== 'locked'">
            <router-link :to="`/practice/${n.node_id}`" class="mini-btn ghost">练</router-link>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.path h1 { margin-bottom: 0.25rem; }
.subtitle { color: #94a3b8; font-size: 0.85rem; margin-bottom: 1rem; }
.subject-tabs { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1.25rem; }
.tab { padding: 0.4rem 0.8rem; border: 1px solid #e2e8f0; background: #fff; border-radius: 20px; font-size: 0.85rem; cursor: pointer; color: #475569; }
.tab.active { background: #4361ee; color: #fff; border-color: #4361ee; }
.next-up { background: #fff; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.25rem; }
.next-up h3 { margin-bottom: 0.75rem; }
.next-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.75rem; }
.next-card { border: 1px solid #f1f5f9; border-top: 3px solid #4361ee; border-radius: 8px; padding: 0.75rem; }
.nc-head { display: flex; justify-content: space-between; align-items: center; gap: 0.3rem; }
.nc-name { font-weight: 600; font-size: 0.9rem; }
.hot { color: #f59e0b; font-size: 0.72rem; flex-shrink: 0; }
.nc-chapter { font-size: 0.75rem; color: #94a3b8; margin: 0.3rem 0 0.6rem; }
.nc-actions { display: flex; gap: 0.4rem; }
.mini-btn { padding: 0.25rem 0.7rem; background: #4361ee; color: #fff; border-radius: 6px; text-decoration: none; font-size: 0.8rem; }
.mini-btn.ghost { background: #f1f5f9; color: #475569; }
.stats { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; font-size: 0.82rem; color: #64748b; }
.stat { display: flex; align-items: center; gap: 0.3rem; }
.stat i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.timeline { background: #fff; border-radius: 12px; padding: 0.5rem 1.25rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.tl-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0; border-bottom: 1px solid #f5f5f5; }
.tl-item:last-child { border-bottom: none; }
.tl-item.locked { opacity: 0.55; }
.tl-dot { width: 24px; height: 24px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; flex-shrink: 0; }
.tl-body { flex: 1; }
.tl-row { display: flex; align-items: center; gap: 0.5rem; }
.tl-name { font-weight: 600; color: #1e293b; font-size: 0.92rem; }
.tl-grade { font-size: 0.72rem; color: #94a3b8; background: #f1f5f9; padding: 0.1rem 0.4rem; border-radius: 8px; }
.tl-state { font-size: 0.75rem; margin-left: auto; }
.tl-sub { font-size: 0.76rem; color: #94a3b8; margin-top: 0.2rem; }
.blocked { color: #ef4444; }
.tl-actions { flex-shrink: 0; }
.loading { text-align: center; padding: 3rem; color: #94a3b8; }
</style>
