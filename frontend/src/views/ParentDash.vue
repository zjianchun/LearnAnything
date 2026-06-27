<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const today = ref<any>(null)
const weekly = ref<any[]>([])
const loading = ref(true)

// AI配置
const aiConfig = ref({ configured: false, model: '', upstream: '', key_preview: '' })
const editModel = ref('')
const editUpstream = ref('')
const editKey = ref('')
const saving = ref(false)
const saveMsg = ref('')

// 学科开关
const allSubjects = ref<string[]>([])
const enabledSubjects = ref<string[]>([])
const subjectSaving = ref(false)

const SUBJECT_LABEL: Record<string, string> = {
  math: '📐 数学', physics: '⚡ 物理', chemistry: '🧪 化学', english: '🔤 英语',
  chinese: '📝 语文', biology: '🌱 生物', geography: '🗺️ 地理', history: '📜 历史',
  politics: '⚖️ 道法',
}

onMounted(async () => {
  const [todayRes, weeklyRes, configRes, subRes] = await Promise.all([
    api.get('/stats/today'),
    api.get('/stats/weekly'),
    api.get('/tutor/config'),
    api.get('/settings/subjects'),
  ])
  today.value = todayRes.data
  weekly.value = weeklyRes.data
  aiConfig.value = configRes.data
  editModel.value = configRes.data.model
  editUpstream.value = configRes.data.upstream
  allSubjects.value = subRes.data.all
  enabledSubjects.value = subRes.data.enabled
  loading.value = false
})

async function toggleSubject(subject: string) {
  subjectSaving.value = true
  const enabled = enabledSubjects.value.includes(subject)
    ? enabledSubjects.value.filter(s => s !== subject)
    : [...enabledSubjects.value, subject]
  try {
    const { data } = await api.put('/settings/subjects', { enabled })
    enabledSubjects.value = data.enabled
  } finally {
    subjectSaving.value = false
  }
}

async function saveConfig() {
  saving.value = true
  saveMsg.value = ''
  try {
    const payload: any = {}
    if (editUpstream.value !== aiConfig.value.upstream) payload.upstream_base = editUpstream.value
    if (editModel.value !== aiConfig.value.model) payload.model = editModel.value
    if (editKey.value) payload.api_key = editKey.value
    const { data } = await api.put('/tutor/config', payload)
    aiConfig.value = data
    editKey.value = ''
    saveMsg.value = '✅ 已保存'
  } catch (e: any) {
    saveMsg.value = '✗ ' + (e?.message || '保存失败')
  } finally {
    saving.value = false
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }
}
</script>

<template>
  <div class="parent-dash">
    <h1>📊 家长看板</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <div class="today-card">
        <h2>今日学习</h2>
        <div class="stats-row">
          <div class="stat">
            <span class="stat-value">{{ (today?.math_minutes || 0) + (today?.physics_minutes || 0) + (today?.english_minutes || 0) }}</span>
            <span class="stat-label">学习分钟</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ today?.questions_total || 0 }}</span>
            <span class="stat-label">做题数</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ today?.questions_total ? Math.round((today.questions_correct / today.questions_total) * 100) : 0 }}%</span>
            <span class="stat-label">正确率</span>
          </div>
        </div>
      </div>

      <div class="subject-rates">
        <div class="rate-card">
          <h3>📐 数学</h3>
          <span class="rate">{{ today?.math_correct_rate ? Math.round(today.math_correct_rate * 100) : '--' }}%</span>
        </div>
        <div class="rate-card">
          <h3>🔬 物理</h3>
          <span class="rate">{{ today?.physics_correct_rate ? Math.round(today.physics_correct_rate * 100) : '--' }}%</span>
        </div>
        <div class="rate-card">
          <h3>🔤 英语</h3>
          <span class="rate">{{ today?.english_correct_rate ? Math.round(today.english_correct_rate * 100) : '--' }}%</span>
        </div>
      </div>

      <div class="weekly-section">
        <h2>近7天趋势</h2>
        <div v-if="weekly.length" class="weekly-list">
          <div v-for="day in weekly" :key="day.date" class="day-row">
            <span class="day-date">{{ day.date.slice(5) }}</span>
            <span class="day-bar">
              <span class="bar" :style="{ width: `${(day.questions_total || 0) * 3}px` }"></span>
            </span>
            <span class="day-count">{{ day.questions_total }}题</span>
            <span class="day-rate">{{ day.questions_total ? Math.round((day.questions_correct / day.questions_total) * 100) : 0 }}%</span>
          </div>
        </div>
        <p v-else class="empty">暂无数据</p>
      </div>

      <!-- 学科开关 -->
      <div class="subject-toggle">
        <h2>📚 学科管理</h2>
        <p class="toggle-hint">关闭的学科将在学生端所有页面隐藏</p>
        <div class="toggle-grid">
          <label v-for="s in allSubjects" :key="s" class="toggle-item" :class="{ off: !enabledSubjects.includes(s) }">
            <input type="checkbox" :checked="enabledSubjects.includes(s)" @change="toggleSubject(s)" :disabled="subjectSaving" />
            <span>{{ SUBJECT_LABEL[s] || s }}</span>
          </label>
        </div>
      </div>

      <!-- AI学伴配置 -->
      <div class="ai-config">
        <h2>🤖 AI学伴配置</h2>
        <p class="config-status">
          状态：<span :class="aiConfig.configured ? 'on' : 'off'">{{ aiConfig.configured ? '已配置' : '未配置' }}</span>
          <span v-if="aiConfig.key_preview" class="key-preview">Key: {{ aiConfig.key_preview }}</span>
        </p>
        <div class="config-form">
          <label>API端点
            <input v-model="editUpstream" placeholder="https://api.minimaxi.com/v1" />
          </label>
          <label>模型名称
            <input v-model="editModel" placeholder="MiniMax-Text-01" />
          </label>
          <label>API Key（留空不改）
            <input v-model="editKey" type="password" placeholder="sk-xxx..." />
          </label>
          <div class="config-actions">
            <button @click="saveConfig" :disabled="saving">{{ saving ? '保存中...' : '保存配置' }}</button>
            <span class="save-msg">{{ saveMsg }}</span>
          </div>
        </div>
        <p class="config-hint">支持任何 OpenAI 兼容 API（MiniMax、DeepSeek、通义千问、GPT等）。修改即时生效，重启服务后回退到.env默认值。</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.parent-dash h1 { margin-bottom: 1.5rem; }
.today-card {
  background: #fff; border-radius: 12px; padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.5rem;
}
.stats-row { display: flex; gap: 2rem; margin-top: 1rem; }
.stat { display: flex; flex-direction: column; align-items: center; }
.stat-value { font-size: 2rem; font-weight: 700; color: #4361ee; }
.stat-label { font-size: 0.8rem; color: #888; }
.subject-rates { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.rate-card {
  background: #fff; border-radius: 12px; padding: 1rem; text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.rate-card h3 { font-size: 0.9rem; margin-bottom: 0.5rem; }
.rate { font-size: 1.5rem; font-weight: 700; color: #333; }
.weekly-section { background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.weekly-section h2 { margin-bottom: 1rem; font-size: 1.1rem; }
.day-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.4rem 0; }
.day-date { width: 3rem; font-size: 0.85rem; color: #666; }
.bar { display: inline-block; height: 12px; background: #4361ee; border-radius: 6px; min-width: 4px; }
.day-count { font-size: 0.8rem; color: #666; width: 3rem; }
.day-rate { font-size: 0.8rem; color: #22c55e; }
.loading { text-align: center; padding: 3rem; color: #999; }
.empty { color: #aaa; }

/* AI配置 */
.ai-config { background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-top: 1.5rem; }

/* 学科开关 */
.subject-toggle { background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-top: 1.5rem; }
.subject-toggle h2 { font-size: 1.1rem; margin-bottom: 0.3rem; }
.toggle-hint { font-size: 0.78rem; color: #94a3b8; margin-bottom: 1rem; }
.toggle-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 0.6rem; }
.toggle-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 8px; cursor: pointer; font-size: 0.88rem; background: #f0fdf4; border: 1px solid #bbf7d0; transition: all 0.2s; }
.toggle-item.off { background: #f8fafc; border-color: #e2e8f0; opacity: 0.6; }
.toggle-item input { accent-color: #22c55e; }
.ai-config h2 { font-size: 1.1rem; margin-bottom: 0.75rem; }
.config-status { font-size: 0.85rem; color: #64748b; margin-bottom: 1rem; }
.config-status .on { color: #22c55e; font-weight: 600; }
.config-status .off { color: #ef4444; font-weight: 600; }
.key-preview { margin-left: 1rem; font-family: monospace; font-size: 0.8rem; color: #94a3b8; }
.config-form { display: flex; flex-direction: column; gap: 0.75rem; }
.config-form label { font-size: 0.82rem; color: #475569; display: flex; flex-direction: column; gap: 0.3rem; }
.config-form input { padding: 0.5rem 0.75rem; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.88rem; font-family: monospace; }
.config-actions { display: flex; align-items: center; gap: 1rem; margin-top: 0.5rem; }
.config-actions button { padding: 0.5rem 1.2rem; background: #4361ee; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 0.85rem; }
.config-actions button:disabled { background: #cbd5e1; }
.save-msg { font-size: 0.82rem; color: #22c55e; }
.config-hint { font-size: 0.75rem; color: #94a3b8; margin-top: 0.75rem; }
</style>
