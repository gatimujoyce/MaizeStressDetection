import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Maize Stress Monitor',
        short_name: 'MaizeMonitor',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        theme_color: '#2e7d32',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' }
        ],
        screenshots: [
          {
            src: 'screenshots/desktop.png',
            sizes: '1280x720',
            type: 'image/png',
            form_factor: 'wide',
            label: 'Maize Stress Monitor Desktop Dashboard'
          },
          {
            src: 'screenshots/mobile.png',
            sizes: '750x1334',
            type: 'image/png',
            label: 'Maize Stress Monitor Mobile View'
          }
        ]
      }
    })
  ]
})