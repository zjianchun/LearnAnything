<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()

const subjects = ref<any[]>([])
const subject = ref<string>((route.params.subject as string) || 'math')
const mapData = ref<any>(null)
const loading = ref(true)
const selected = ref<any>(null)
const detail = ref<any>(null)

// 布局常量
const COL_W = 210      // 年级列宽
const NODE_W = 168
const NODE_H = 46
const ROW_H = 64
const PAD_X = 24
const LANE_GAP = 40    // domain泳道间距
const HEADER_H = 34    // 泳道标题高度

const grades = [7, 8, 9]

onMounted(async () => {
  const { data } = await api.get('/graph/subjects')
  subjects.value = data
  await loadMap()
})

watch(subject, loadMap)

async function loadMap() {
  loading.value = true
  selected.value = null
  detail.value = null
  const { data } = await api.get(`/graph/map/${subject.value}`)
  mapData.value = data
  loading.value = false
}

function masteryColor(m: number): string {
  if (m >= 0.8) return '#22c55e'
  if (m >= 0.5) return '#eab308'
  if (m > 0) return '#ef4444'
  return '#cbd5e1'
}

// 计算每个节点的 x/y 坐标
const layout = computed(() => {
  if (!mapData.value) return { positions: {}, lanes: [], width: 0, height: 0 }
  const positions: Record<string, { x: number; y: number; node: any }> = {}
  const lanes: any[] = []
  let curY = 40   // 顶部预留年级标题带
  const gradeX = (g: number) => PAD_X + grades.indexOf(g) * COL_W

  // 按 domain 分组
  const byDomain: Record<string, any[]> = {}
  for (const n of mapData.value.nodes) {
    const d = n.domain || 'other'
    ;(byDomain[d] ||= []).push(n)
  }
  const domainOrder = mapData.value.domains.map((d: any) => d.id)

  for (const dId of domainOrder) {
    const dNodes = byDomain[dId] || []
    const dInfo = mapData.value.domains.find((x: any) => x.id === dId)
    const laneTop = curY
    // 每个年级一列，列内堆叠
    let maxStack = 0
    for (const g of grades) {
      const cell = dNodes.filter((n: any) => n.grade === g)
        .sort((a: any, b: any) => (a.semester - b.semester) || a.name.localeCompare(b.name))
      cell.forEach((n: any, i: number) => {
        positions[n.node_id] = {
          x: gradeX(g),
          y: laneTop + HEADER_H + i * ROW_H,
          node: n,
        }
      })
      maxStack = Math.max(maxStack, cell.length)
    }
    const laneHeight = HEADER_H + Math.max(maxStack, 1) * ROW_H
    lanes.push({ id: dId, name: dInfo?.name || dId, top: laneTop, height: laneHeight })
    curY = laneTop + laneHeight + LANE_GAP
  }

  const width = PAD_X * 2 + grades.length * COL_W
  return { positions, lanes, width, height: curY }
})

const edges = computed(() => {
  if (!mapData.value) return []
  const pos = layout.value.positions
  const out: any[] = []
  for (const e of mapData.value.edges) {
    const from = pos[e.from], to = pos[e.to]
    if (!from || !to) continue
    // 从 prereq 右侧中点 → 节点 左侧中点（贝塞尔）
    const x1 = from.x + NODE_W, y1 = from.y + NODE_H / 2
    const x2 = to.x, y2 = to.y + NODE_H / 2
    const mx = (x1 + x2) / 2
    out.push({ d: `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}` })
  }
  return out
})

async function selectNode(n: any) {
  selected.value = n
  detail.value = null
  const { data } = await api.get(`/graph/node/${n.node_id}`)
  detail.value = data
}

function gradeLabel(g: number) {
  return { 7: '初一', 8: '初二', 9: '初三' }[g] || `${g}年级`
}
</script>

<template>
  <div class="kmap">
    <h1>🗺️ 知识地图</h1>

    <!-- 学科切换 -->
    <div class="subject-tabs">
      <button v-for="s in subjects" :key="s.subject"
        class="tab" :class="{ active: s.subject === subject }"
        @click="subject = s.subject">
        {{ s.icon }} {{ s.name }}
        <span class="tab-count">{{ s.mastered }}/{{ s.total }}</span>
      </button>
    </div>

    <p class="legend">
      <span><i style="background:#22c55e"></i>掌握</span>
      <span><i style="background:#eab308"></i>半会</span>
      <span><i style="background:#ef4444"></i>薄弱</span>
      <span><i style="background:#cbd5e1"></i>未学</span>
      <span class="legend-hint">点节点看详情 · 横轴为年级 · 连线为前置依赖</span>
    </p>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="map-wrap">
      <!-- 地图画布 -->
      <div class="canvas-scroll">
        <svg :width="layout.width" :height="layout.height" class="canvas">
          <!-- 年级列标题 -->
          <g v-for="(g, i) in grades" :key="'col'+g">
            <rect :x="PAD_X + i * COL_W - 4" :y="6" :width="NODE_W + 8" :height="26" rx="6" class="col-bg" />
            <text :x="PAD_X + i * COL_W + NODE_W/2" :y="19" class="col-label">{{ gradeLabel(g) }}</text>
          </g>
          <!-- domain泳道 -->
          <g v-for="lane in layout.lanes" :key="lane.id">
            <rect :x="0" :y="lane.top" :width="layout.width" :height="lane.height"
              class="lane-bg" rx="8" />
            <text :x="10" :y="lane.top + 20" class="lane-label">{{ lane.name }}</text>
          </g>
          <!-- 依赖边 -->
          <path v-for="(e, i) in edges" :key="'e'+i" :d="e.d" class="edge" />
          <!-- 节点 -->
          <g v-for="(p, nid) in layout.positions" :key="nid"
            :transform="`translate(${p.x},${p.y})`"
            class="node" :class="{ sel: selected?.node_id === nid }"
            @click="selectNode(p.node)">
            <rect :width="NODE_W" :height="NODE_H" rx="8"
              :style="{ stroke: masteryColor(p.node.mastery) }" class="node-box" />
            <circle :cx="14" :cy="NODE_H/2" r="5" :fill="masteryColor(p.node.mastery)" />
            <text :x="26" :y="NODE_H/2 - 2" class="node-name">{{ p.node.name }}</text>
            <text :x="26" :y="NODE_H/2 + 14" class="node-sub">
              {{ p.node.exam_weight === 'high' ? '★高频' : '' }}
              {{ Math.round(p.node.mastery * 100) }}%
            </text>
          </g>
        </svg>
      </div>

      <!-- 详情面板 -->
      <aside v-if="selected" class="detail-panel">
        <button class="close" @click="selected = null">×</button>
        <h3>{{ selected.name }}</h3>
        <p class="chapter">{{ detail?.chapter }}</p>
        <div v-if="detail">
          <div class="badge-row">
            <span class="badge" :style="{ background: masteryColor(detail.mastery) + '22', color: masteryColor(detail.mastery) }">
              掌握度 {{ Math.round(detail.mastery * 100) }}%
            </span>
            <span class="badge weight" v-if="detail.exam_weight === 'high'">★ 高频考点 {{ detail.exam_points }}分</span>
          </div>

          <div class="sect" v-if="detail.prerequisites?.length">
            <h4>前置知识</h4>
            <span v-for="p in detail.prerequisites" :key="p.node_id" class="chip"
              :style="{ borderColor: masteryColor(p.mastery) }">{{ p.name }} {{ Math.round(p.mastery*100) }}%</span>
          </div>
          <div class="sect" v-if="detail.successors?.length">
            <h4>后继知识</h4>
            <span v-for="s in detail.successors" :key="s.node_id" class="chip">{{ s.name }}</span>
          </div>
          <div class="sect" v-if="detail.curriculum_points?.length">
            <h4>课标要求</h4>
            <ul class="cp"><li v-for="(c,i) in detail.curriculum_points" :key="i">{{ c }}</li></ul>
          </div>

          <div class="actions">
            <router-link v-if="detail.question_count > 0" :to="`/practice/${detail.node_id}`" class="btn">
              ✏️ 做题 ({{ detail.question_count }})
            </router-link>
            <router-link :to="`/learn/${detail.node_id}`" class="btn ghost">📖 学课件</router-link>
          </div>
        </div>
        <div v-else class="loading-sm">加载详情...</div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.kmap h1 { margin-bottom: 1rem; }
.subject-tabs { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.75rem; }
.tab {
  padding: 0.4rem 0.8rem; border: 1px solid #e2e8f0; background: #fff; border-radius: 20px;
  font-size: 0.85rem; cursor: pointer; transition: all 0.15s; color: #475569;
}
.tab:hover { border-color: #4361ee; }
.tab.active { background: #4361ee; color: #fff; border-color: #4361ee; }
.tab-count { opacity: 0.7; font-size: 0.75rem; margin-left: 0.2rem; }
.legend { display: flex; gap: 1rem; align-items: center; font-size: 0.8rem; color: #64748b; margin-bottom: 0.75rem; flex-wrap: wrap; }
.legend span { display: flex; align-items: center; gap: 0.3rem; }
.legend i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.legend-hint { color: #94a3b8; }
.map-wrap { display: flex; gap: 1rem; }
.canvas-scroll { flex: 1; overflow: auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); max-height: calc(100vh - 230px); }
.canvas { display: block; }
.col-bg { fill: #eef2ff; }
.col-label { font-size: 13px; font-weight: 700; fill: #4361ee; text-anchor: middle; dominant-baseline: middle; }
.lane-bg { fill: #f8fafc; }
.lane-label { font-size: 12px; font-weight: 600; fill: #94a3b8; dominant-baseline: hanging; }
.edge { fill: none; stroke: #cbd5e1; stroke-width: 1.5; opacity: 0.6; }
.node { cursor: pointer; }
.node-box { fill: #fff; stroke-width: 2; transition: all 0.1s; }
.node:hover .node-box { fill: #f1f5ff; }
.node.sel .node-box { fill: #eef2ff; stroke-width: 3; }
.node-name { font-size: 12.5px; fill: #1e293b; font-weight: 600; dominant-baseline: middle; }
.node-sub { font-size: 10px; fill: #94a3b8; dominant-baseline: middle; }
.detail-panel {
  width: 300px; flex-shrink: 0; background: #fff; border-radius: 12px; padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); position: relative; max-height: calc(100vh - 230px); overflow-y: auto;
}
.close { position: absolute; top: 0.75rem; right: 0.75rem; border: none; background: none; font-size: 1.3rem; cursor: pointer; color: #94a3b8; }
.detail-panel h3 { margin-bottom: 0.25rem; padding-right: 1.5rem; }
.chapter { font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.75rem; }
.badge-row { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 1rem; }
.badge { padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.78rem; font-weight: 600; }
.badge.weight { background: #fef3c7; color: #b45309; }
.sect { margin-bottom: 1rem; }
.sect h4 { font-size: 0.85rem; color: #475569; margin-bottom: 0.4rem; }
.chip { display: inline-block; padding: 0.2rem 0.55rem; margin: 0.2rem 0.2rem 0 0; border: 1.5px solid #e2e8f0; border-radius: 12px; font-size: 0.78rem; color: #475569; }
.cp { margin: 0; padding-left: 1.1rem; }
.cp li { font-size: 0.8rem; color: #64748b; margin-bottom: 0.3rem; line-height: 1.4; }
.actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.btn { flex: 1; text-align: center; padding: 0.5rem; background: #4361ee; color: #fff; border-radius: 8px; text-decoration: none; font-size: 0.85rem; }
.btn.ghost { background: #f1f5f9; color: #475569; }
.loading, .loading-sm { text-align: center; padding: 2rem; color: #94a3b8; }
</style>
