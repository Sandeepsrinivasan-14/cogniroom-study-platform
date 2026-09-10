import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: true,
    watch: {
      ignored: ['**/GrShaderCache/**']
    }
  },
  plugins: [react()],
  css: {
    postcss: {}
  }
})
