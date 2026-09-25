// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vuetify from 'vite-plugin-vuetify'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { Vuetify3Resolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    vuetify({ autoImport: true }),
    AutoImport({
      imports: ['vue','vue-router','pinia','@vueuse/core',{ axios: [['default','axios']] }],
      dts: 'src/auto-imports.d.ts',
      eslintrc: { enabled: true, filepath: './.eslintrc-auto-import.json', globalsPropValue: true },
    }),
    Components({
      dirs: ['src/components'],
      extensions: ['vue'],
      deep: true,
      resolvers: [Vuetify3Resolver()],
      dts: 'src/components.d.ts',
    }),
  ],

  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
      '~styles': new URL('./src/assets/styles', import.meta.url).pathname,
    },
  },

  css: {
    preprocessorOptions: {
      scss: {},
    },
  },

  server: {
    host: true,
    port: Number(process.env.VITE_DEV_PORT) || 520,
    open: false,  // 不自动打开浏览器，通过HTTPS代理访问
    hmr: { 
      overlay: true,
      clientPort: 5200,  // 通过HTTPS代理的端口
      protocol: 'wss'    // 使用安全WebSocket
    },
    proxy: {
      // 代理 API 请求到 Django
      '/api': {
        target: process.env.VITE_API_BASE_URL?.replace('/api', '') || 'http://web-dev:911',
        changeOrigin: true,
        secure: false,  // 开发环境下允许自签名证书
        rewrite: (path) => path,  // 保持 /api 路径
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('代理错误:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('发送请求:', req.method, req.url, '-> 目标:', proxyReq.getHeader('host') + proxyReq.path);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('收到响应:', proxyRes.statusCode, req.url);
          });
        },
      },
      // 代理 /media 静态文件到 Django
      '/media': {
        target: process.env.VITE_API_BASE_URL?.replace('/api', '') || 'http://web-dev:911',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,  // 保持 /media/... 不变
      },
      // 代理 admin 到 Django
      '/admin': {
        target: process.env.VITE_API_BASE_URL?.replace('/api', '') || 'http://web-dev:911',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,  // 保持 /admin 路径
      },
    },
  },

  build: {
    outDir: 'dist',
  },
})
