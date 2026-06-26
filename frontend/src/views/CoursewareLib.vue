<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import api from '../api'

const subjects = ref<any[]>([])
const subject = ref('math')
const data = ref<any>(null)
const loading = ref(true)
const filter = ref<'all' | 'hosted' | 'available'>('all')

onMounted(async () => {
  const { data: subs } = await api.get('/graph/subjects')
  subjects.value = subs
  await load()
})
watch(subject, load)

async function load() {
  loading.value = true
  const { data: d } = await api.get(`/courseware-api/library/${subject.value}`)
  data.value = d
  loading.value = false
}

const filtered = computed(() => {
  if (!data.value) return []
  if (filter.value === 'hosted') return data.value.items.filter((x: any) => x.self_hosted)
  if (filter.value === 'available') return data.value.items.filter((x: any) => !x.self_hosted && x.available_count)
  return data.value.items
})

function gradeLabel(g: number): string {
  const m: Record<number, string> = { 7: '初一', 8: '初二', 9: '初三' }
  return m[g] || ''
}
</script>

<template>
  <div class="lib">
    <h1>📚 课件库</h1>
    <p class="subtitle">已自托管的可直接学；其余为 teachany.cn 可拉取课件</p>

    <div class="subject-tabs">
      <button v-for="s in subjects" :key="s.subject" class="tab"
        :class="{ active: s.subject === subject }" @click="subject = s.subject">
        {{ s.icon }} {{ s.name }}
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else-if="data">
      <div class="bar">
        <div class="filters">
          <button :class="{ on: filter==='all' }" @click="filter='all'">全部 {{ data.total }}</button>
          <button :class="{ on: filter==='hosted' }" @click="filter='hosted'">已上架 {{ data.hosted }}</button>
          <button :class="{ on: filter==='available' }" @click="filter='available'">可拉取 {{ data.total - data.hosted }}</button>
        </div>
      </div>

      <div class="grid">
        <div v-for="it in filtered" :key="it.node_id" class="card" :class="{ hosted: it.self_hosted }">
          <div class="c-head">
            <span class="c-name">{{ it.name }}</span>
            <span v-if="it.exam_weight==='high'" class="hot">★</span>
          </div>
          <div class="c-meta">{{ gradeLabel(it.grade) }} · {{ it.chapter }}</div>
          <div class="c-foot">
            <span v-if="it.self_hosted" class="badge hosted">✓ 已上架</span>
            <span v-else-if="it.available_count" class="badge avail">⬇ 可拉取 {{ it.available_count }}</span>
            <span v-else class="badge none">待生成</span>
            <router-link v-if="it.self_hosted" :to="`/learn/${it.node_id}`" class="go">去学习 →</router-link>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.lib h1 { margin-bottom: 0.25rem; }
.subtitle { color: #94a3b8; font-size: 0.85rem; margin-bottom: 1rem; }
.subject-tabs { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }
.tab { padding: 0.4rem 0.8rem; border: 1px solid #e2e8f0; background: #fff; border-radius: 20px; font-size: 0.85rem; cursor: pointer; color: #475569; }
.tab.active { background: #4361ee; color: #fff; border-color: #4361ee; }
.bar { margin-bottom: 1rem; }
.filters { display: flex; gap: 0.5rem; }
.filters button { padding: 0.35rem 0.9rem; border: 1px solid #e2e8f0; background: #fff; border-radius: 8px; font-size: 0.82rem; cursor: pointer; color: #64748b; }
.filters button.on { background: #eef2ff; color: #4361ee; border-color: #4361ee; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.85rem; }
.card { background: #fff; border-radius: 10px; padding: 0.9rem 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 3px solid #e2e8f0; }
.card.hosted { border-left-color: #22c55e; }
.c-head { display: flex; justify-content: space-between; align-items: center; }
.c-name { font-weight: 600; color: #1e293b; font-size: 0.95rem; }
.hot { color: #f59e0b; }
.c-meta { font-size: 0.75rem; color: #94a3b8; margin: 0.35rem 0 0.7rem; }
.c-foot { display: flex; justify-content: space-between; align-items: center; }
.badge { font-size: 0.72rem; padding: 0.15rem 0.5rem; border-radius: 10px; }
.badge.hosted { background: #dcfce7; color: #16a34a; }
.badge.avail { background: #eef2ff; color: #4361ee; }
.badge.none { background: #f1f5f9; color: #94a3b8; }
.go { font-size: 0.8rem; color: #4361ee; text-decoration: none; }
.loading { text-align: center; padding: 3rem; color: #94a3b8; }
</style>
