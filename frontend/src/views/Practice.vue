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
const selectedSubject = ref('')
const subjects = ref<any[]>([])

onMounted(async () => {
  if (nodeId.value) {
    await loadQuestions()
  } else {
    await loadSubjects()
  }
})

async function loadSubjects() {
  const { data } = await api.get('/graph/subjects')
  subjects.value = data
  loading.value = false
}

async function selectSubject(subject: string) {
  selectedSubject.value = subject
  loading.value = true
  const { data } = await api.get(`/questions/nodes/${subject}`)
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

    <!-- 科目选择 -->
    <div v-else-if="!selectedSubject && !nodeId" class="subject-select">
      <h1>✏️ 选择练习科目</h1>
      <div class="subject-grid">
        <div v-for="s in subjects" :key="s.subject" class="subject-card" @click="selectSubject(s.subject)">
          <span class="subject-icon">{{ s.icon }}</span>
          <span class="subject-name">{{ s.name }}</span>
          <span class="subject-total">{{ s.total }}个知识点</span>
        </div>
      </div>
    </div>

    <!-- 知识点选择 -->
    <div v-else-if="!nodeId" class="node-select">
      <h1>
        <span class="back-link" @click="selectedSubject=''; nodeList=[]">← </span>
        选择练习知识点
      </h1>
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
.practice { padding-top: 0.5rem; }

/* 科目选择 */
.subject-select h1 {
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin-bottom: 1.25rem;
}
.subject-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}
.subject-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 1.2rem 0.5rem;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.subject-card:active { transform: scale(0.95); }
.subject-icon { font-size: 1.8rem; }
.subject-name { font-weight: 600; font-size: 0.85rem; color: var(--color-text); }
.subject-total { font-size: 0.68rem; color: var(--color-text-muted); }

/* 返回 */
.back-link {
  cursor: pointer;
  color: var(--color-primary);
  font-size: 1.1rem;
}

/* 知识点选择 */
.node-select h1 {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 1rem;
}
.node-list { display: flex; flex-direction: column; gap: 0.6rem; }
.node-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 0.9rem 1rem;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: transform 0.1s ease;
}
.node-card:active { transform: scale(0.98); }
.node-info { display: flex; flex-direction: column; }
.node-name { font-weight: 600; font-size: 0.9rem; color: var(--color-text); }
.node-chapter { font-size: 0.72rem; color: var(--color-text-muted); margin-top: 0.15rem; }
.node-meta { display: flex; align-items: center; gap: 0.6rem; }
.q-count { font-size: 0.75rem; color: var(--color-text-secondary); }
.mastery-badge {
  padding: 0.2rem 0.55rem;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* 做题卡 */
.question-card, .result-card, .empty-state {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 1.5rem 1.25rem;
  box-shadow: var(--shadow-md);
}

.progress-bar {
  height: 5px;
  background: var(--color-border);
  border-radius: 3px;
  margin-bottom: 1rem;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
  border-radius: 3px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.meta {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-bottom: 1rem;
}

.question-text {
  font-size: 1.05rem;
  line-height: 1.7;
  margin-bottom: 1.25rem;
  color: var(--color-text);
}

.question-figure {
  max-width: 100%;
  max-height: 280px;
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
  border: 1px solid var(--color-border);
}

.figure-desc {
  font-size: 0.82rem;
  color: var(--color-text-secondary);
  background: var(--color-primary-bg);
  padding: 0.6rem 1rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  border-left: 3px solid var(--color-primary);
}

/* 选项 */
.options { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.25rem; }
.option {
  padding: 0.8rem 1rem;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.95rem;
}
.option:active { transform: scale(0.98); }
.option.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-bg);
}

.answer-input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 1rem;
  margin-bottom: 1rem;
  outline: none;
  transition: border-color 0.2s;
}
.answer-input:focus { border-color: var(--color-primary); }

/* 按钮 */
.submit-btn, .next-btn, .action-btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s ease;
}
.submit-btn:hover, .next-btn:hover { background: #5a4bd6; }
.submit-btn:disabled { background: var(--color-text-muted); cursor: not-allowed; }
.action-btn.secondary { background: var(--color-text-secondary); }
.result-actions { display: flex; gap: 0.75rem; margin-top: 1.5rem; }

/* 反馈 */
.feedback {
  margin-top: 1.25rem;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-md);
}
.feedback.correct { background: #f0fdf4; border: 1.5px solid #86efac; }
.feedback.wrong { background: #fef2f2; border: 1.5px solid #fca5a5; }
.feedback-title { font-weight: 600; font-size: 1rem; margin-bottom: 0.3rem; }
.hint { color: #b45309; margin-top: 0.5rem; font-size: 0.88rem; }
.steps { margin-top: 0.75rem; font-size: 0.85rem; line-height: 1.6; }

/* 结果 */
.score {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}
.result-card h2 { margin-bottom: 0.5rem; }

/* 加载/空 */
.loading { text-align: center; padding: 3rem; color: var(--color-text-muted); }
.empty-state { text-align: center; padding: 3rem; }

/* 讲解 */
.explain-area { margin-top: 0.75rem; }
.explain-btn {
  padding: 0.5rem 1rem;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  text-decoration: none;
  display: inline-block;
}
.explain-btn:disabled { opacity: 0.6; cursor: wait; }
.explain-btn.ready { background: var(--color-accent); }
</style>
