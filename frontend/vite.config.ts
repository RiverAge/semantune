import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// import path from 'path'

// https://vitejs.dev/config/
declare const __dirname: string;
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': __dirname + '/src',
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Sending request to the target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('Received response from the target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
})
