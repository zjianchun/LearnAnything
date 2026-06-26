<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const overview = ref<any>(null)
const loading = ref(true)
const testMode = ref(false)
const testQuestions = ref<any[]>([])
const current = ref(0)
const userAnswer = ref('')
const answers = ref<any[]>([])
const submitting = ref(false)

onMounted(async () => {
  const { data } = await api.get('/diagnosis/overview')
  overview.value = data
  loading.value = false
})

async function startDiagnosis() {
  loading.value = true
  const { data } = await api.get('/diagnosis/generate/math')
  testQuestions.value = data.questions
  testMode.value = true
  loading.value = false
}

function selectAnswer(answer: string) {
  userAnswer.value = answer
}

function submitCurrent() {
  const q = testQuestions.value[current.value]
  answers.value.push({
    node_id: q.node_id,
    question_id: q.id,
    correct: userAnswer.value.trim() === '', // will be determined by backend
    user_answer: userAnswer.value,
  })
  userAnswer.value = ''
  current.value++

  if (current.value >= testQuestions.value.length) {
    finishTest()
  }
}

async function finishTest() {
  submitting.value = true
  // Submit each answer to check and record
  for (const ans of answers.value) {
    await api.post('/questions/check', {
      question_id: ans.question_id,
      node_id: ans.node_id,
      user_answer: ans.user_answer,
    })
  }
  // Refresh overview
  const { data } = await api.get('/diagnosis/overview')
  overview.value = data
  testMode.value = false
  submitting.value = false
}

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

    <div v-if="loading" class="loading">加载中...</div>

    <!-- 诊断测试模式 -->
    <div v-else-if="testMode && !submitting" class="test-mode">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${(current / testQuestions.length) * 100}%` }"></div>
      </div>
      <p class="meta">
        第 {{ current + 1 }}/{{ testQuestions.length }} 题 ·
        {{ testQuestions[current].node_name }} · {{ testQuestions[current].chapter }}
      </p>

      <div class="question-card">
        <div class="question-text">{{ testQuestions[current].question }}</div>

        <div v-if="testQuestions[current].options?.length" class="options">
          <label v-for="(opt, i) in testQuestions[current].options" :key="i"
            class="option" :class="{ selected: userAnswer === opt }" @click="selectAnswer(opt)">
            {{ opt }}
          </label>
        </div>
        <input v-else v-model="userAnswer" placeholder="输入答案" class="answer-input"
          @keyup.enter="submitCurrent" />

        <button @click="submitCurrent" :disabled="!userAnswer" class="submit-btn">
          {{ current < testQuestions.length - 1 ? '下一题 →' : '完成诊断' }}
        </button>
      </div>
    </div>

    <!-- 提交中 -->
    <div v-else-if="submitting" class="loading">正在分析诊断结果...</div>

    <!-- 概览模式 -->
    <div v-else>
      <p class="subtitle">绿色=掌握 · 黄色=半会 · 红色=薄弱 · 灰色=未学</p>

      <button @click="startDiagnosis" class="start-btn">🧪 开始入学诊断（数学）</button>

      <div class="subjects">
        <div v-for="(nodes, subject) in overview" :key="subject" class="subject-section">
          <h2>
            <span v-if="subject === 'math'">📐 数学</span>
            <span v-else-if="subject === 'physics'">🔬 物理</span>
            <span v-else>🔤 英语</span>
          </h2>
          <div class="node-grid">
            <router-link v-for="node in nodes" :key="node.node_id"
              :to="`/practice/${node.node_id}`" class="node-chip"
              :style="{ borderColor: statusColor(node.mastery) }">
              <span class="dot" :style="{ background: statusColor(node.mastery) }"></span>
              {{ node.name }}
              <span class="pct">{{ Math.round(node.mastery * 100) }}%</span>
            </router-link>
          </div>
          <p v-if="!nodes?.length" class="empty">暂无数据，请先完成入学诊断</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.diagnosis h1 { margin-bottom: 0.25rem; }
.subtitle { color: #888; font-size: 0.85rem; margin-bottom: 1rem; }
.start-btn {
  display: inline-block; padding: 0.75rem 1.5rem; background: #4361ee; color: #fff;
  border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; margin-bottom: 2rem;
}
.start-btn:hover { background: #3451d1; }
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
.test-mode { max-width: 640px; margin: 0 auto; }
.progress-bar { height: 4px; background: #e0e0e0; border-radius: 2px; margin-bottom: 1rem; }
.progress-fill { height: 100%; background: #4361ee; border-radius: 2px; transition: width 0.3s; }
.meta { font-size: 0.85rem; color: #888; margin-bottom: 1rem; }
.question-card {
  background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.question-text { font-size: 1.1rem; line-height: 1.6; margin-bottom: 1.5rem; }
.options { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; }
.option {
  padding: 0.75rem 1rem; border: 2px solid #e8e8e8; border-radius: 8px; cursor: pointer;
}
.option:hover { border-color: #4361ee; }
.option.selected { border-color: #4361ee; background: #eef2ff; }
.answer-input {
  width: 100%; padding: 0.75rem; border: 2px solid #e8e8e8; border-radius: 8px;
  font-size: 1rem; margin-bottom: 1rem;
}
.submit-btn {
  padding: 0.7rem 1.5rem; background: #4361ee; color: #fff;
  border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer;
}
.submit-btn:disabled { background: #ccc; cursor: not-allowed; }
.loading { text-align: center; padding: 3rem; color: #999; }
.empty { color: #aaa; }
</style>
