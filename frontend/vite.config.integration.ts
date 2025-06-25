/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Custom plugin to log HTTP requests
function requestLoggerPlugin() {
  return {
    name: 'request-logger',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const start = Date.now()
        const timestamp = new Date().toISOString()
        
        // Log the incoming request
        console.log(`[${timestamp}] Vite: ${req.method} ${req.url}`)
        
        // Override res.end to log response
        const originalEnd = res.end
        res.end = function(...args) {
          const duration = Date.now() - start
          console.log(`[${new Date().toISOString()}] Vite: ${req.method} ${req.url} - ${res.statusCode} (${duration}ms)`)
          return originalEnd.apply(this, args)
        }
        
        next()
      })
    }
  }
}

// Integration test configuration with enhanced logging
export default defineConfig({
  plugins: [react(), requestLoggerPlugin()],
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
