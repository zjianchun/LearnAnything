<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { renderLatex } from '../utils/latex'

const route = useRoute()
const router = useRouter()
const nodeId = ref(route.params.nodeId as string || '')
const questions = ref<any[]>([])
const current = ref(0)
const userAnswer = ref('')
const feedback = ref<any>(null)
const loading = ref(true)
const mastery = ref(0)
const score = ref({ correct: 0, total: 0 })
const nodeList = ref<any[]>([])
const explaining = ref(false)
const explainUrl = ref('')

onMounted(async () => {
  if (nodeId.value) {
    await loadQuestions()
  } else {
    await loadNodeList()
  }
})

async function loadNodeList() {
  const { data } = await api.get('/questions/nodes/math')
  nodeList.value = data
  loading.value = false
}

async function loadQuestions() {
  loading.value = true
  const { data } = await api.get(`/questions/practice/${nodeId.value}`)
  questions.value = data.questions
  mastery.value = data.mastery
  loading.value = false
}

function selectNode(nid: string) {
  nodeId.value = nid
  router.push(`/practice/${nid}`)
  loadQuestions()
}

async function submitAnswer() {
  const q = questions.value[current.value]
  const { data } = await api.post('/questions/check', {
    question_id: q.id,
    node_id: nodeId.value,
    user_answer: userAnswer.value,
  })
  feedback.value = data
  score.value.total++
  if (data.correct) score.value.correct++
}

function next() {
  feedback.value = null
  userAnswer.value = ''
  explainUrl.value = ''
  current.value++
}

async function getExplain() {
  const q = questions.value[current.value]
  explaining.value = true
  try {
    const { data } = await api.post('/explain/generate', {
      question_id: q.id,
      question: q.question,
      answer: feedback.value?.correct_answer || q.answer,
      user_answer: userAnswer.value,
      node_name: q.node_name || nodeId.value,
      subject: q.subject || 'math',
    })
    if (data.ok) explainUrl.value = data.learn_url
  } finally {
    explaining.value = false
  }
}

function restart() {
  current.value = 0
  score.value = { correct: 0, total: 0 }
  feedback.value = null
  userAnswer.value = ''
  loadQuestions()
}
</script>

<template>
  <div class="practice">
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 知识点选择 -->
    <div v-else-if="!nodeId" class="node-select">
      <h1>✏️ 选择练习知识点</h1>
      <div class="node-list">
        <div v-for="node in nodeList" :key="node.node_id" class="node-card" @click="selectNode(node.node_id)">
          <div class="node-info">
            <span class="node-name">{{ node.name }}</span>
            <span class="node-chapter">{{ node.chapter }}</span>
          </div>
          <div class="node-meta">
            <span class="q-count">{{ node.question_count }}题</span>
            <span class="mastery-badge" :style="{ background: node.mastery >= 0.8 ? '#dcfce7' : node.mastery > 0 ? '#fef9c3' : '#f3f4f6' }">
              {{ Math.round(node.mastery * 100) }}%
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 练习完成 -->
    <div v-else-if="current >= questions.length && questions.length > 0" class="result-card">
      <h2>🎉 练习完成！</h2>
      <p class="score">正确率：{{ score.total > 0 ? Math.round(score.correct / score.total * 100) : 0 }}%</p>
      <p>{{ score.correct }}/{{ score.total }} 题正确</p>
      <div class="result-actions">
        <button @click="restart" class="action-btn">🔄 再练一组</button>
        <router-link to="/" class="action-btn secondary">返回首页</router-link>
      </div>
    </div>

    <!-- 无题目 -->
    <div v-else-if="questions.length === 0" class="empty-state">
      <p>📭 该知识点暂无题目</p>
      <router-link to="/practice" class="action-btn">← 选择其他知识点</router-link>
    </div>

    <!-- 做题中 -->
    <div v-else class="question-card">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${(current / questions.length) * 100}%` }"></div>
      </div>
      <p class="meta">第 {{ current + 1 }}/{{ questions.length }} 题 · 难度 {{ '⭐'.repeat(questions[current].difficulty) }}</p>

      <div class="question-text" v-html="renderLatex(questions[current].question)"></div>

      <!-- 题目配图 -->
      <img v-if="questions[current].figure_url" :src="questions[current].figure_url" class="question-figure" alt="题目图片" />
      <p v-else-if="questions[current].figure_description" class="figure-desc">📐 {{ questions[current].figure_description }}</p>

      <div v-if="questions[current].options?.length" class="options">
        <label v-for="(opt, i) in questions[current].options" :key="i" class="option"
          :class="{ selected: userAnswer === opt }" @click="!feedback && (userAnswer = opt)">
          <span v-html="renderLatex(opt)"></span>
        </label>
      </div>
      <input v-else v-model="userAnswer" placeholder="输入答案" class="answer-input"
        :disabled="!!feedback" @keyup.enter="!feedback && submitAnswer()" />

      <button v-if="!feedback" @click="submitAnswer" :disabled="!userAnswer" class="submit-btn">提交答案</button>

      <div v-if="feedback" class="feedback" :class="{ correct: feedback.correct, wrong: !feedback.correct }">
        <p class="feedback-title">{{ feedback.correct ? '✅ 正确！' : '❌ 错误' }}</p>
        <p v-if="!feedback.correct">正确答案：{{ feedback.correct_answer }}</p>
        <p v-if="feedback.hint" class="hint">💡 {{ feedback.hint }}</p>
        <div v-if="feedback.steps?.length" class="steps">
          <p><strong>解题步骤：</strong></p>
          <ol><li v-for="s in feedback.steps" :key="s">{{ s }}</li></ol>
        </div>
        <button @click="next" class="next-btn">{{ current < questions.length - 1 ? '下一题 →' : '查看结果' }}</button>
        <div v-if="!feedback.correct" class="explain-area">
          <button v-if="!explainUrl" @click="getExplain" :disabled="explaining" class="explain-btn">
            {{ explaining ? '生成讲解中...' : '📖 看详细讲解' }}
          </button>
          <router-link v-else :to="explainUrl" class="explain-btn ready">📖 查看讲解 →</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.practice { max-width: 640px; margin: 0 auto; }
.node-select h1 { margin-bottom: 1.5rem; }
.node-list { display: flex; flex-direction: column; gap: 0.75rem; }
.node-card {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff; border-radius: 12px; padding: 1rem 1.25rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); cursor: pointer; transition: transform 0.1s;
}
.node-card:hover { transform: translateX(4px); }
.node-info { display: flex; flex-direction: column; }
.node-name { font-weight: 600; color: #333; }
.node-chapter { font-size: 0.8rem; color: #888; margin-top: 0.2rem; }
.node-meta { display: flex; align-items: center; gap: 0.75rem; }
.q-count { font-size: 0.8rem; color: #666; }
.mastery-badge { padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
.question-card, .result-card, .empty-state {
  background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.progress-bar { height: 4px; background: #e0e0e0; border-radius: 2px; margin-bottom: 1rem; }
.progress-fill { height: 100%; background: #4361ee; border-radius: 2px; transition: width 0.3s; }
.meta { font-size: 0.85rem; color: #888; margin-bottom: 1rem; }
.question-text { font-size: 1.1rem; line-height: 1.6; margin-bottom: 1.5rem; }
.question-figure { max-width: 100%; max-height: 300px; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #e2e8f0; }
.figure-desc { font-size: 0.85rem; color: #64748b; background: #f8fafc; padding: 0.6rem 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 3px solid #4361ee; }
.options { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; }
.option {
  padding: 0.75rem 1rem; border: 2px solid #e8e8e8; border-radius: 8px; cursor: pointer; transition: all 0.15s;
}
.option:hover { border-color: #4361ee; }
.option.selected { border-color: #4361ee; background: #eef2ff; }
.answer-input {
  width: 100%; padding: 0.75rem; border: 2px solid #e8e8e8; border-radius: 8px; font-size: 1rem; margin-bottom: 1rem;
}
.submit-btn, .next-btn, .action-btn {
  display: inline-block; padding: 0.7rem 1.5rem; background: #4361ee; color: #fff;
  border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer; text-decoration: none;
}
.action-btn.secondary { background: #6b7280; }
.submit-btn:disabled { background: #ccc; cursor: not-allowed; }
.result-actions { display: flex; gap: 1rem; margin-top: 1.5rem; }
.feedback { margin-top: 1rem; padding: 1rem; border-radius: 8px; }
.feedback.correct { background: #f0fdf4; border: 1px solid #86efac; }
.feedback.wrong { background: #fef2f2; border: 1px solid #fca5a5; }
.hint { color: #b45309; margin-top: 0.5rem; }
.steps { margin-top: 0.75rem; font-size: 0.9rem; }
.score { font-size: 2rem; font-weight: 700; color: #4361ee; }
.loading { text-align: center; padding: 3rem; color: #999; }
.empty-state { text-align: center; padding: 3rem; }
.explain-area { margin-top: 0.75rem; }
.explain-btn { padding: 0.5rem 1rem; background: #7c3aed; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 0.85rem; text-decoration: none; display: inline-block; }
.explain-btn:disabled { background: #a78bfa; cursor: wait; }
.explain-btn.ready { background: #22c55e; }
</style>
