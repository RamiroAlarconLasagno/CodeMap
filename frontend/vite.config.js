// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Todas las llamadas a /api/* se redirigen al backend FastAPI
      '/carpetas':    { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/clases':      { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/metodos':     { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/funciones':   { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/imports':     { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/variables':   { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/llamadas':    { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/usos':        { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/libreria':    { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/buscar':      { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/idioma':      { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/estado':      { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/reanalizar':  { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/exportar':    { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/carpeta':     { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})