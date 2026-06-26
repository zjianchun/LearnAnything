<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()
const nodeId = route.params.nodeId as string
const loading = ref(true)
const node = ref<any>(null)
const coursewareUrl = ref('')
const hasContent = ref(false)

onMounted(async () => {
  try {
    const { data } = await api.get(`/graph/node/${nodeId}`)
    node.value = data
    // 自托管课件约定路径：/courseware/<subject>/<node_id>/index.html
    const url = `/courseware/${data.subject}/${nodeId}/index.html`
    // 探测课件是否存在
    try {
      const head = await fetch(url, { method: 'HEAD' })
      hasContent.value = head.ok
      if (head.ok) coursewareUrl.value = url
    } catch {
      hasContent.value = false
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="learn">
    <div class="learn-header">
      <router-link to="/" class="back">← 返回</router-link>
      <span class="title">{{ node?.name || '' }}</span>
      <router-link :to="`/practice/${nodeId}`" class="practice-link">去做题 ✏️</router-link>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <iframe v-else-if="hasContent" :src="coursewareUrl" class="courseware-frame" />

    <div v-else class="no-content">
      <h2>📚 该知识点课件待生成</h2>
      <p>「{{ node?.name }}」的互动课件还没有制作。</p>
      <p class="hint" v-if="node?.teachany_node">官方课件标识：{{ node.teachany_node }}（可从 teachany.cn 拉取）</p>
      <router-link :to="`/practice/${nodeId}`" class="practice-link big">先去做题练习 →</router-link>
    </div>
  </div>
</template>

<style scoped>
.learn { display: flex; flex-direction: column; height: calc(100vh - 100px); }
.learn-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 0; margin-bottom: 0.5rem; gap: 1rem;
}
.back { text-decoration: none; color: #666; }
.title { font-weight: 600; color: #1e293b; flex: 1; text-align: center; }
.practice-link {
  padding: 0.5rem 1rem; background: #4361ee; color: #fff;
  border-radius: 6px; text-decoration: none; font-size: 0.9rem;
}
.practice-link.big { display: inline-block; margin-top: 1.5rem; padding: 0.75rem 1.5rem; }
.courseware-frame {
  flex: 1; border: none; border-radius: 12px; background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.no-content {
  text-align: center; padding: 4rem 2rem; background: #fff;
  border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.no-content h2 { margin-bottom: 1rem; }
.hint { font-size: 0.85rem; color: #94a3b8; margin-top: 0.5rem; }
.loading { text-align: center; padding: 3rem; color: #94a3b8; }
</style>
