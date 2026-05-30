import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['host.docker.internal', 'localhost', 'frontend'],
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:80',
        changeOrigin: true,
      },
    },
    watch: {
      usePolling: true,
    },
  },
})
