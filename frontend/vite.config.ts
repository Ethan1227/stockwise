import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // 前端代理 /api 到后端 8000
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
