<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/', icon: '🏠', label: '首页' },
  { path: '/graph', icon: '🧭', label: '全科图谱' },
  { path: '/practice', icon: '✏️', label: '练习' },
  { path: '/memory', icon: '🧠', label: '记忆训练' },
  { path: '/library', icon: '📖', label: '课件库' },
  { path: '/path', icon: '🗺️', label: '学习路径' },
  { path: '/diagnosis', icon: '🎯', label: '学情诊断' },
  { path: '/errors', icon: '📝', label: '错题本' },
  { path: '/pbl', icon: '🔬', label: 'PBL探究' },
  { path: '/progress', icon: '📊', label: '我的进度' },
]

const mobileNav = navItems.slice(0, 5)

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <div class="app-shell">
    <!-- 侧边栏 (平板/电脑) -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-icon">⚡</span>
        <span class="brand-text">WayToSuper</span>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main class="main-area">
      <router-view />
    </main>

    <!-- 底部 Tab (仅手机) -->
    <nav class="mobile-tab">
      <router-link
        v-for="item in mobileNav"
        :key="item.path"
        :to="item.path"
        class="tab-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="tab-icon">{{ item.icon }}</span>
        <span class="tab-label">{{ item.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<style>
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
  --sidebar-w: 240px;
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
.app-shell {
  min-height: 100dvh;
  display: flex;
}

/* ===== 侧边栏 (>=768px 显示) ===== */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-w);
  height: 100dvh;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0.75rem;
  z-index: 100;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0 0.75rem;
  margin-bottom: 2rem;
}
.brand-icon { font-size: 1.5rem; }
.brand-text {
  font-size: 1.1rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-1);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.65rem 0.75rem;
  border-radius: var(--radius-sm);
  text-decoration: none;
  color: var(--text-2);
  font-size: 0.88rem;
  font-weight: 500;
  transition: all 0.3s var(--ease);
}
.nav-item:hover {
  background: var(--accent-soft);
  color: var(--accent);
}
.nav-item.active {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 700;
}
.nav-icon { font-size: 1.15rem; width: 24px; text-align: center; }
.nav-label { white-space: nowrap; }

/* ===== 主内容区 ===== */
.main-area {
  flex: 1;
  margin-left: var(--sidebar-w);
  padding: 2rem 3rem;
  max-width: 820px;
}

/* ===== 底部 Tab (仅手机) ===== */
.mobile-tab {
  display: none;
}

/* ===== 响应式 ===== */

/* 平板竖屏 */
@media (max-width: 1024px) {
  :root { --sidebar-w: 200px; }
  .main-area { padding: 1.5rem 2rem; }
}

/* 手机 */
@media (max-width: 768px) {
  .sidebar { display: none; }

  .main-area {
    margin-left: 0;
    padding: 1rem 1.25rem 5.5rem;
    max-width: 100%;
  }

  .mobile-tab {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-around;
    align-items: center;
    height: 64px;
    background: var(--surface);
    border-top: 1px solid var(--border);
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
    color: var(--text-3);
    font-size: 0.62rem;
    font-weight: 500;
    padding: 0.4rem 0.6rem;
    border-radius: var(--radius-sm);
    transition: all 0.3s var(--ease);
  }
  .tab-icon { font-size: 1.3rem; transition: transform 0.3s var(--ease); }
  .tab-label { letter-spacing: 0.01em; }
  .tab-item.active { color: var(--accent); }
  .tab-item.active .tab-icon { transform: translateY(-2px) scale(1.1); }
}
</style>
