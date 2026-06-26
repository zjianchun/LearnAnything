<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()
const nodeId = route.params.nodeId as string
const questions = ref<any[]>([])
const current = ref(0)
const userAnswer = ref('')
const feedback = ref<any>(null)
const loading = ref(true)
const mastery = ref(0)
const score = ref({ correct: 0, total: 0 })

onMounted(async () => {
  const { data } = await api.get(`/questions/practice/${nodeId}`)
  questions.value = data.questions
  mastery.value = data.mastery
  loading.value = false
})

async function submitAnswer() {
  const q = questions.value[current.value]
  const { data } = await api.post('/questions/check', {
    question_id: q.id,
    node_id: nodeId,
    user_answer: userAnswer.value,
  })
  feedback.value = data
  score.value.total++
  if (data.correct) score.value.correct++

  // 同时上报诊断
  await api.post('/diagnosis/submit', [{
    node_id: nodeId,
    question_id: q.id,
    correct: data.correct ? 1 : 0,
    error_type: data.error_type,
  }])
}

function next() {
  feedback.value = null
  userAnswer.value = ''
  current.value++
}
</script>

<template>
  <div class="practice">
    <div v-if="loading" class="loading">加载题目中...</div>

    <div v-else-if="current >= questions.length" class="result-card">
      <h2>🎉 练习完成！</h2>
      <p class="score">正确率：{{ score.total > 0 ? Math.round(score.correct / score.total * 100) : 0 }}%</p>
      <p>{{ score.correct }}/{{ score.total }} 题正确</p>
      <router-link to="/" class="back-btn">返回首页</router-link>
    </div>

    <div v-else class="question-card">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${(current / questions.length) * 100}%` }"></div>
      </div>
      <p class="meta">第 {{ current + 1 }}/{{ questions.length }} 题 · 难度 {{ '⭐'.repeat(questions[current].difficulty) }}</p>

      <div class="question-text">{{ questions[current].question }}</div>

      <div v-if="questions[current].options?.length" class="options">
        <label v-for="(opt, i) in questions[current].options" :key="i" class="option"
          :class="{ selected: userAnswer === opt }">
          <input type="radio" :value="opt" v-model="userAnswer" :disabled="!!feedback" />
          {{ opt }}
        </label>
      </div>
      <input v-else v-model="userAnswer" placeholder="输入答案" class="answer-input" :disabled="!!feedback" />

      <button v-if="!feedback" @click="submitAnswer" :disabled="!userAnswer" class="submit-btn">提交答案</button>

      <div v-if="feedback" class="feedback" :class="{ correct: feedback.correct, wrong: !feedback.correct }">
        <p class="feedback-title">{{ feedback.correct ? '✅ 正确！' : '❌ 错误' }}</p>
        <p v-if="!feedback.correct">正确答案：{{ feedback.correct_answer }}</p>
        <p v-if="feedback.hint" class="hint">💡 {{ feedback.hint }}</p>
        <div v-if="feedback.steps?.length" class="steps">
          <p><strong>解题步骤：</strong></p>
          <ol><li v-for="s in feedback.steps" :key="s">{{ s }}</li></ol>
        </div>
        <button @click="next" class="next-btn">下一题 →</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.practice { max-width: 640px; margin: 0 auto; }
.question-card, .result-card {
  background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.progress-bar { height: 4px; background: #e0e0e0; border-radius: 2px; margin-bottom: 1rem; }
.progress-fill { height: 100%; background: #4361ee; border-radius: 2px; transition: width 0.3s; }
.meta { font-size: 0.85rem; color: #888; margin-bottom: 1rem; }
.question-text { font-size: 1.1rem; line-height: 1.6; margin-bottom: 1.5rem; }
.options { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; }
.option {
  padding: 0.75rem 1rem; border: 2px solid #e8e8e8; border-radius: 8px; cursor: pointer; transition: all 0.15s;
}
.option:hover { border-color: #4361ee; }
.option.selected { border-color: #4361ee; background: #eef2ff; }
.answer-input {
  width: 100%; padding: 0.75rem; border: 2px solid #e8e8e8; border-radius: 8px; font-size: 1rem; margin-bottom: 1rem;
}
.submit-btn, .next-btn, .back-btn {
  display: inline-block; padding: 0.7rem 1.5rem; background: #4361ee; color: #fff;
  border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer; text-decoration: none;
}
.submit-btn:disabled { background: #ccc; cursor: not-allowed; }
.feedback { margin-top: 1rem; padding: 1rem; border-radius: 8px; }
.feedback.correct { background: #f0fdf4; border: 1px solid #86efac; }
.feedback.wrong { background: #fef2f2; border: 1px solid #fca5a5; }
.hint { color: #b45309; margin-top: 0.5rem; }
.steps { margin-top: 0.75rem; font-size: 0.9rem; }
.score { font-size: 2rem; font-weight: 700; color: #4361ee; }
.loading { text-align: center; padding: 3rem; color: #999; }
</style>
