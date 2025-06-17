/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to Flask backend
      '/api': 'http://localhost:5000',
      '/auth': 'http://localhost:5000',
      '/uploads': 'http://localhost:5000',
      '/health': 'http://localhost:5000'
    }
  },
  build: {
    outDir: '../kiosk_show_replacement/static/dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        // Ensure consistent file naming for Flask integration
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  }
})
