import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(() => {
  // Support GitHub Pages repository subpath (/placemental-portal/) while preserving '/' for local dev and unified Render builds
  const isGhPages = process.env.VITE_DEPLOY_TARGET === 'gh-pages' || process.env.GITHUB_PAGES === 'true';
  const basePath = process.env.VITE_BASE_PATH || (isGhPages ? '/placemental-portal/' : '/');

  return {
    base: basePath,
    plugins: [react()],
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor-react': ['react', 'react-dom', 'react-router-dom'],
            'vendor-charts': ['recharts'],
            'vendor-ui': ['lucide-react', 'framer-motion'],
          }
        }
      }
    }
  };
})
