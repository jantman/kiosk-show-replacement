/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Custom plugin to log HTTP requests with cookie debugging
function requestLoggerPlugin() {
  return {
    name: 'request-logger',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const start = Date.now()
        const timestamp = new Date().toISOString()

        // Log the incoming request with cookie info
        const cookies = req.headers.cookie || 'no-cookies'
        console.log(`[${timestamp}] Vite: ${req.method} ${req.url} (cookies: ${cookies.substring(0, 50)}...)`)

        // Capture original setHeader to log Set-Cookie responses
        const originalSetHeader = res.setHeader.bind(res)
        res.setHeader = function(name, value) {
          if (name.toLowerCase() === 'set-cookie') {
            console.log(`[${new Date().toISOString()}] Vite: Set-Cookie from backend: ${JSON.stringify(value).substring(0, 100)}...`)
          }
          return originalSetHeader(name, value)
        }

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
  // Note: We don't set base here for integration tests because:
  // 1. The dev server handles routing differently than production builds
  // 2. Setting base: '/admin/' causes Vite to show an error page when
  //    React Router navigates to paths without trailing slashes
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to Flask backend with proper cookie handling
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        // Ensure cookies work across different ports during testing
        cookieDomainRewrite: '',
      },
      '/auth': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/uploads': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/health': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        cookieDomainRewrite: '',
      }
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
