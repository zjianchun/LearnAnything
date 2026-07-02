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
/* ===== Global Reset & Design Tokens ===== */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --font: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;
  --bg: #F8F9FA;
  --surface: #FFFFFF;
  --text-1: #1A1A2E;
  --text-2: #4A4A68;
  --text-3: #9B9BB4;
  --accent: #5B4CDB;
  --accent-soft: #EEEDFC;
  --success: #2ECC87;
  --success-soft: #E8F9F0;
  --warning: #F5A623;
  --danger: #E74C5F;
  --border: #F0F0F5;
  --shadow-xs: 0 1px 3px rgba(90, 76, 219, 0.03);
  --shadow-sm: 0 2px 8px rgba(90, 76, 219, 0.04), 0 1px 2px rgba(0,0,0,0.02);
  --shadow-md: 0 4px 24px rgba(90, 76, 219, 0.06), 0 2px 8px rgba(0,0,0,0.02);
  --shadow-lg: 0 12px 48px rgba(90, 76, 219, 0.08), 0 4px 12px rgba(0,0,0,0.03);
  --radius-sm: 12px;
  --radius-md: 18px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  --ease: cubic-bezier(0.32, 0.72, 0, 1);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text-1);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.5;
}

.tabular-nums { font-variant-numeric: tabular-nums; }
</style>

<style scoped>
.app {
  min-height: 100dvh;
  padding-bottom: 80px;
}

.main-content {
  max-width: 440px;
  margin: 0 auto;
  padding: 1.25rem 1.25rem 2rem;
}

/* ===== Tab Bar ===== */
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.25rem;
  height: 68px;
  max-width: 400px;
  width: calc(100% - 2rem);
  padding: 0 0.5rem;
  background: var(--surface);
  border-radius: 22px 22px 0 0;
  box-shadow: 0 -8px 40px rgba(90, 76, 219, 0.06), 0 -2px 8px rgba(0,0,0,0.02);
  z-index: 1000;
  padding-bottom: env(safe-area-inset-bottom);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  text-decoration: none;
  color: var(--text-3);
  font-size: 0.62rem;
  font-weight: 500;
  padding: 0.5rem 0;
  border-radius: var(--radius-sm);
  transition: all 0.5s var(--ease);
}

.tab-icon {
  font-size: 1.3rem;
  transition: transform 0.5s var(--ease);
}

.tab-label {
  letter-spacing: 0.01em;
}

.tab-item.active {
  color: var(--accent);
}

.tab-item.active .tab-icon {
  transform: translateY(-2px) scale(1.1);
}
</style>
