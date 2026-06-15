import { fileURLToPath, URL } from 'node:url'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev server proxies the API and health check to the FastAPI backend so the SPA
// runs same-origin in development (SSE + X-User-Id work with no CORS friction).
// In the recorded demo the built app is served by FastAPI itself (single origin).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8002', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8002', changeOrigin: true },
    },
  },
})
