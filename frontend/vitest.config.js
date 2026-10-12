import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
    globalSetup: ['./tests/global-setup.js'],
    env: {
      VITE_BACKEND_URL: 'http://127.0.0.1:5055',
    },
  },
})
