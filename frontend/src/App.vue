<script setup lang="ts">
</script>

<template>
  <div class="app">
    <nav class="nav-bar">
      <router-link to="/" class="nav-brand">📚 LearnAnything</router-link>
      <div class="nav-links">
        <router-link to="/">首页</router-link>
        <router-link to="/graph">全科图谱</router-link>
        <router-link to="/map">知识地图</router-link>
        <router-link to="/path">学习路径</router-link>
        <router-link to="/library">课件库</router-link>
        <router-link to="/pbl">PBL探究</router-link>
        <router-link to="/memory">记忆</router-link>
        <router-link to="/diagnosis">诊断</router-link>
        <router-link to="/practice">练习</router-link>
        <router-link to="/errors">错题本</router-link>
        <router-link to="/progress">进度</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: #f5f7fa;
}
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-brand {
  font-size: 1.25rem;
  font-weight: 700;
  text-decoration: none;
  color: #1a1a2e;
}
.nav-links {
  display: flex;
  gap: 1.25rem;
}
.nav-links a {
  text-decoration: none;
  color: #555;
  font-size: 0.9rem;
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  transition: all 0.2s;
}
.nav-links a:hover,
.nav-links a.router-link-active {
  color: #4361ee;
  background: #eef2ff;
}
.main-content {
  max-width: 960px;
  margin: 0 auto;
  padding: 1.5rem;
}
</style>
