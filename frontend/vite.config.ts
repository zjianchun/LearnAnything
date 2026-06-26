import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    // WSL2 在 /mnt/c (Windows挂载盘) 上 inotify 失效，需轮询监听才能热更新
    watch: {
      usePolling: true,
      interval: 300,
    },
    proxy: {
      '/api': 'http://localhost:8000',
      '/courseware': 'http://localhost:8000',
    }
  }
})
