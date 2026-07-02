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
.memory { padding-top: 0.5rem; }
.memory h1 { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 0.5rem; }

.tabs { display: flex; gap: 0.3rem; flex-wrap: wrap; margin-bottom: 1.5rem; align-items: center; }
.tabs button {
  padding: 0.4rem 0.7rem; border: 1.5px solid var(--border); background: var(--surface);
  border-radius: 20px; font-size: 0.78rem; cursor: pointer; font-weight: 600; font-family: var(--font);
  transition: all 0.3s var(--ease);
}
.tabs button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.mode-switch { margin-left: auto; display: flex; gap: 0.2rem; }
.mode-switch button { padding: 0.3rem 0.6rem; font-size: 0.7rem; border-radius: 6px; }

.progress-text { font-size: 0.75rem; color: var(--text-3); margin-bottom: 1rem; font-weight: 500; font-variant-numeric: tabular-nums; }

.flip-card {
  min-height: 220px; background: var(--surface); border-radius: var(--radius-xl); box-shadow: var(--shadow-lg);
  display: flex; align-items: center; justify-content: center; padding: 2.5rem 2rem;
  cursor: pointer; font-size: 1.2rem; font-weight: 600; color: var(--text-1); text-align: center;
  transition: transform 0.5s var(--ease); line-height: 1.6;
}
.flip-card:active { transform: scale(0.97); }
.flip-card .card-back { display: none; color: var(--accent); }
.flip-card.flipped .card-front { display: none; }
.flip-card.flipped .card-back { display: block; }
.flip-card.flipped { cursor: default; background: var(--success-soft); }

.action-row { display: flex; gap: 0.75rem; justify-content: center; margin-top: 1.25rem; }
.btn-wrong, .btn-right {
  padding: 0.7rem 1.8rem; border-radius: 28px; font-size: 0.88rem; font-weight: 700;
  cursor: pointer; transition: transform 0.3s var(--ease); font-family: var(--font);
}
.btn-wrong:active, .btn-right:active { transform: scale(0.93); }
.btn-wrong { background: #FEF2F2; color: var(--danger); border: 1.5px solid #FECACA; }
.btn-right { background: var(--success-soft); color: #059669; border: 1.5px solid #A7F3D0; }

.hint { text-align: center; color: var(--text-3); font-size: 0.78rem; margin-top: 1rem; font-weight: 500; }

.spell-area { text-align: center; }
.spell-prompt {
  font-size: 1.15rem; font-weight: 700; color: var(--text-1); background: var(--surface);
  border-radius: var(--radius-xl); padding: 2rem 1.5rem; box-shadow: var(--shadow-lg); margin-bottom: 1.25rem;
}
.spell-input {
  width: 100%; max-width: 280px; padding: 0.8rem 1rem; border: 1.5px solid var(--border);
  border-radius: 28px; font-size: 1rem; text-align: center; font-family: var(--font);
  outline: none; transition: border-color 0.3s var(--ease);
}
.spell-input:focus { border-color: var(--accent); }
.spell-input.correct { border-color: var(--success); background: var(--success-soft); }
.spell-input.wrong { border-color: var(--danger); background: #FEF2F2; }

.spell-btn {
  margin-top: 0.75rem; padding: 0.6rem 1.5rem; background: var(--accent); color: #fff; border: none;
  border-radius: 28px; font-size: 0.85rem; font-weight: 700; cursor: pointer; font-family: var(--font);
}
.spell-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.spell-feedback { margin-top: 1rem; font-size: 0.9rem; }
.next-btn {
  margin-top: 0.75rem; padding: 0.55rem 1.2rem; background: var(--accent); color: #fff; border: none;
  border-radius: 20px; cursor: pointer; font-weight: 600; font-size: 0.82rem; font-family: var(--font);
}

.done-card {
  text-align: center; padding: 3rem 1.5rem; background: var(--surface);
  border-radius: var(--radius-xl); box-shadow: var(--shadow-lg);
}
.done-card h2 { font-size: 1.3rem; font-weight: 800; margin-bottom: 0.5rem; }
.stats-bar { margin-top: 1rem; font-size: 0.78rem; color: var(--text-3); font-weight: 500; }
.green { color: var(--success); }
.yellow { color: var(--warning); }

.loading, .empty { text-align: center; padding: 3rem; color: var(--text-3); font-weight: 500; }
</style>
