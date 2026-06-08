import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/',
  server: {
    proxy: {
      '/api': 'http://localhost:8501',
      '/avatar': 'http://localhost:8501',
      '/login': 'http://localhost:8501',
      '/logout': 'http://localhost:8501',
    }
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  }
})
