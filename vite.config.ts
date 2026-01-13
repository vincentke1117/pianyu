import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  server: {
    port: 3000,
    host: '0.0.0.0',
  },
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
      '@components': path.resolve(__dirname, './components'),
      '@hooks': path.resolve(__dirname, './hooks'),
      '@context': path.resolve(__dirname, './context'),
      '@types': path.resolve(__dirname, './types'),
    },
  },
  build: {
    // 代码分割优化
    rollupOptions: {
      output: {
        // 将大型依赖单独打包
        manualChunks: {
          // React 相关库
          'react-vendor': ['react', 'react-dom', 'react-markdown'],
          // UI 图标库
          'ui-vendor': ['lucide-react'],
        },
        // 资源文件命名
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },
    // 使用 esbuild 压缩（默认）
    minify: 'esbuild',
    // chunk 大小警告阈值 (KB)
    chunkSizeWarningLimit: 1000,
  },
  // 优化依赖预构建
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-markdown', 'lucide-react'],
  },
});
