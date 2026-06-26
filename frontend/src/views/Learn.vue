<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const nodeId = route.params.nodeId as string
const coursewareUrl = ref(`/courseware/${nodeId.replace(/^(math|physics|english)-[mh]-/, '$1/')}/index.html`)
const hasContent = ref(true)
</script>

<template>
  <div class="learn">
    <div class="learn-header">
      <router-link to="/" class="back">← 返回</router-link>
      <router-link :to="`/practice/${nodeId}`" class="practice-link">去做题 ✏️</router-link>
    </div>

    <iframe
      v-if="hasContent"
      :src="coursewareUrl"
      class="courseware-frame"
      @error="hasContent = false"
    />

    <div v-else class="no-content">
      <h2>📚 课件生成中...</h2>
      <p>该知识点的互动课件正在制作中，请先前往做题练习。</p>
      <router-link :to="`/practice/${nodeId}`" class="practice-link">开始练习 →</router-link>
    </div>
  </div>
</template>

<style scoped>
.learn { display: flex; flex-direction: column; height: calc(100vh - 100px); }
.learn-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 0; margin-bottom: 0.5rem;
}
.back { text-decoration: none; color: #666; }
.practice-link {
  padding: 0.5rem 1rem; background: #4361ee; color: #fff;
  border-radius: 6px; text-decoration: none; font-size: 0.9rem;
}
.courseware-frame {
  flex: 1; border: none; border-radius: 12px; background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.no-content {
  text-align: center; padding: 4rem 2rem; background: #fff;
  border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.no-content h2 { margin-bottom: 1rem; }
</style>
