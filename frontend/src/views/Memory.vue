<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const subjects = ['english', 'history', 'politics', 'chinese']
const SUBJECT_LABEL: Record<string, string> = { english: '🔤 英语', history: '📜 历史', politics: '⚖️ 道法', chinese: '📝 语文' }
const subject = ref('english')
const queue = ref<any[]>([])
const current = ref(0)
const flipped = ref(false)
const spellInput = ref('')
const spellResult = ref<null | boolean>(null)
const mode = ref<'flip' | 'spell'>('flip')
const stats = ref<any>(null)
const loading = ref(true)
const sessionCorrect = ref(0)
const sessionTotal = ref(0)

const card = computed(() => queue.value[current.value])
const progress = computed(() => queue.value.length ? `${current.value + 1} / ${queue.value.length}` : '0 / 0')

onMounted(() => load())

async function load() {
  loading.value = true
  const [qRes, sRes] = await Promise.all([
    api.get(`/memory/today?subject=${subject.value}&limit=30`),
    api.get(`/memory/stats?subject=${subject.value}`),
  ])
  const d = qRes.data
  queue.value = [...d.due.map((x: any) => ({ ...x, card_id: x.card_id })),
                 ...d.new.map((x: any) => ({ ...x, card_id: x.id, front: x.front, back: x.back }))]
  stats.value = sRes.data
  current.value = 0; flipped.value = false; spellInput.value = ''; spellResult.value = null
  sessionCorrect.value = 0; sessionTotal.value = 0
  loading.value = false
}

async function answer(correct: boolean) {
  if (!card.value) return
  sessionTotal.value++
  if (correct) sessionCorrect.value++
  await api.post('/memory/review', { card_id: card.value.card_id, correct })
  next()
}

function checkSpell() {
  if (!card.value) return
  const ans = card.value.back.split(/[;；,，/]/)[0].trim().toLowerCase()
  const input = spellInput.value.trim().toLowerCase()
  spellResult.value = input === ans
  sessionTotal.value++
  if (spellResult.value) sessionCorrect.value++
  api.post('/memory/review', { card_id: card.value.card_id, correct: spellResult.value })
}

function next() {
  flipped.value = false; spellInput.value = ''; spellResult.value = null
  current.value++
}

function switchSubject(s: string) { subject.value = s; load() }
</script>

<template>
  <div class="memory">
    <h1>📇 记忆训练</h1>

    <div class="tabs">
      <button v-for="s in subjects" :key="s" :class="{ active: subject === s }" @click="switchSubject(s)">{{ SUBJECT_LABEL[s] }}</button>
      <div class="mode-switch">
        <button :class="{ active: mode==='flip' }" @click="mode='flip'">翻卡</button>
        <button :class="{ active: mode==='spell' }" @click="mode='spell'">拼写</button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <!-- 完成 -->
    <div v-else-if="current >= queue.length" class="done-card">
      <h2>🎉 今日任务完成！</h2>
      <p>正确率：{{ sessionTotal ? Math.round(sessionCorrect / sessionTotal * 100) : 0 }}% ({{ sessionCorrect }}/{{ sessionTotal }})</p>
      <div v-if="stats" class="stats-bar">
        <span>总卡片 {{ stats.total }}</span> · <span class="green">已掌握 {{ stats.mastered }}</span> ·
        <span class="yellow">学习中 {{ stats.learning }}</span> · <span>待学 {{ stats.not_started }}</span>
      </div>
    </div>

    <!-- 训练中 -->
    <div v-else-if="card" class="card-area">
      <p class="progress-text">{{ progress }} · 本次正确 {{ sessionCorrect }}/{{ sessionTotal }}</p>

      <!-- 翻卡模式 -->
      <div v-if="mode==='flip'" class="flip-card" :class="{ flipped }" @click="!flipped && (flipped=true)">
        <div class="card-front">{{ card.front }}</div>
        <div class="card-back">{{ card.back }}</div>
      </div>
      <div v-if="mode==='flip' && flipped" class="action-row">
        <button class="btn-wrong" @click="answer(false)">❌ 没记住</button>
        <button class="btn-right" @click="answer(true)">✅ 记住了</button>
      </div>
      <p v-if="mode==='flip' && !flipped" class="hint">点击卡片翻转查看答案</p>

      <!-- 拼写模式 -->
      <div v-if="mode==='spell'" class="spell-area">
        <div class="spell-prompt">{{ card.front }}</div>
        <input v-model="spellInput" placeholder="输入答案..." @keyup.enter="spellResult===null && checkSpell()"
          :disabled="spellResult!==null" class="spell-input" :class="{ correct: spellResult===true, wrong: spellResult===false }" />
        <button v-if="spellResult===null" @click="checkSpell" :disabled="!spellInput.trim()" class="spell-btn">检查</button>
        <div v-else class="spell-feedback">
          <p v-if="spellResult">✅ 正确！</p>
          <p v-else>❌ 正确答案：<strong>{{ card.back }}</strong></p>
          <button @click="next" class="next-btn">下一个 →</button>
        </div>
      </div>
    </div>

    <div v-else class="empty">暂无卡片，请等待数据生成</div>
  </div>
</template>

<style scoped>
.memory h1 { margin-bottom: 0.5rem; }
.tabs { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 1.25rem; align-items: center; }
.tabs button { padding: 0.4rem 0.8rem; border: 1px solid #e2e8f0; background: #fff; border-radius: 20px; font-size: 0.85rem; cursor: pointer; }
.tabs button.active { background: #4361ee; color: #fff; border-color: #4361ee; }
.mode-switch { margin-left: auto; display: flex; gap: 0.3rem; }
.mode-switch button { padding: 0.3rem 0.7rem; font-size: 0.78rem; border-radius: 6px; }
.progress-text { font-size: 0.82rem; color: #64748b; margin-bottom: 1rem; }
.flip-card { min-height: 200px; background: #fff; border-radius: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); display: flex; align-items: center; justify-content: center; padding: 2rem; cursor: pointer; font-size: 1.3rem; color: #1e293b; text-align: center; position: relative; transition: transform 0.3s; }
.flip-card .card-back { display: none; color: #4361ee; }
.flip-card.flipped .card-front { display: none; }
.flip-card.flipped .card-back { display: block; }
.flip-card.flipped { cursor: default; background: #f0fdf4; }
.action-row { display: flex; gap: 1rem; justify-content: center; margin-top: 1.25rem; }
.btn-wrong { padding: 0.6rem 1.5rem; background: #fef2f2; color: #dc2626; border: 2px solid #fca5a5; border-radius: 10px; font-size: 1rem; cursor: pointer; }
.btn-right { padding: 0.6rem 1.5rem; background: #f0fdf4; color: #16a34a; border: 2px solid #86efac; border-radius: 10px; font-size: 1rem; cursor: pointer; }
.hint { text-align: center; color: #94a3b8; font-size: 0.85rem; margin-top: 1rem; }
.spell-area { text-align: center; }
.spell-prompt { font-size: 1.3rem; font-weight: 600; color: #1e293b; background: #fff; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 16px rgba(0,0,0,0.08); margin-bottom: 1.25rem; }
.spell-input { width: 100%; max-width: 320px; padding: 0.7rem 1rem; border: 2px solid #e2e8f0; border-radius: 10px; font-size: 1.1rem; text-align: center; }
.spell-input.correct { border-color: #22c55e; background: #f0fdf4; }
.spell-input.wrong { border-color: #ef4444; background: #fef2f2; }
.spell-btn { margin-top: 0.75rem; padding: 0.5rem 1.5rem; background: #4361ee; color: #fff; border: none; border-radius: 8px; font-size: 0.9rem; cursor: pointer; }
.spell-feedback { margin-top: 1rem; }
.next-btn { margin-top: 0.75rem; padding: 0.5rem 1.2rem; background: #4361ee; color: #fff; border: none; border-radius: 8px; cursor: pointer; }
.done-card { text-align: center; padding: 3rem; background: #fff; border-radius: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.stats-bar { margin-top: 1rem; font-size: 0.85rem; color: #64748b; }
.green { color: #22c55e; } .yellow { color: #eab308; }
.loading, .empty { text-align: center; padding: 3rem; color: #94a3b8; }
</style>
