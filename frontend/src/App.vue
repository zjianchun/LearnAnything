<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

const tabs = [
  { path: '/', icon: '🏠', label: '首页' },
  { path: '/graph', icon: '🧭', label: '图谱' },
  { path: '/practice', icon: '✏️', label: '练习' },
  { path: '/memory', icon: '🧠', label: '记忆' },
  { path: '/progress', icon: '📊', label: '我的' },
]

const currentTab = computed(() => {
  return tabs.find(t => t.path === route.path)?.path || ''
})
</script>

<template>
  <div class="app">
    <main class="main-content">
      <router-view />
    </main>

    <!-- 底部导航栏 -->
    <nav class="tab-bar">
      <router-link
        v-for="tab in tabs"
        :key="tab.path"
        :to="tab.path"
        class="tab-item"
        :class="{ active: currentTab === tab.path }"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<style>
/* ===== 全局样式重置 ===== */
:root {
  --color-primary: #6C5CE7;
  --color-primary-light: #A29BFE;
  --color-primary-bg: #F8F7FF;
  --color-accent: #00B894;
  --color-accent-light: #55EFC4;
  --color-warning: #FDCB6E;
  --color-danger: #FF7675;
  --color-success: #00B894;
  --color-bg: #FAFBFC;
  --color-surface: #FFFFFF;
  --color-text: #2D3436;
  --color-text-secondary: #636E72;
  --color-text-muted: #B2BEC3;
  --color-border: #F0F0F3;
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-xl: 28px;
  --shadow-sm: 0 2px 8px rgba(108, 92, 231, 0.06);
  --shadow-md: 0 4px 16px rgba(108, 92, 231, 0.08);
  --shadow-lg: 0 8px 32px rgba(108, 92, 231, 0.12);
  --font-body: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-body);
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  line-height: 1.6;
}

/* 数字等宽 */
.tabular-nums { font-variant-numeric: tabular-nums; }
</style>

<style scoped>
.app {
  min-height: 100vh;
  min-height: 100dvh;
  padding-bottom: 72px;
  background: var(--color-bg);
}

.main-content {
  max-width: 480px;
  margin: 0 auto;
  padding: 1rem 1rem 2rem;
}

/* ===== 底部 Tab Bar ===== */
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 64px;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.04);
  z-index: 1000;
  padding-bottom: env(safe-area-inset-bottom);
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  text-decoration: none;
  color: var(--color-text-muted);
  font-size: 0.65rem;
  padding: 0.4rem 0.8rem;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
  position: relative;
}

.tab-icon {
  font-size: 1.4rem;
  transition: transform 0.2s ease;
}

.tab-label {
  font-weight: 500;
  letter-spacing: 0.02em;
}

.tab-item.active {
  color: var(--color-primary);
}

.tab-item.active .tab-icon {
  transform: scale(1.15);
}

.tab-item.active::after {
  content: '';
  position: absolute;
  top: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: var(--color-primary);
  border-radius: 0 0 3px 3px;
}
</style>
