import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://iotcoss.nexcode.kr:8000',
      '/ws': {
        target: 'ws://iotcoss.nexcode.kr:8000',
        ws: true,
      },
    },
  },
})
