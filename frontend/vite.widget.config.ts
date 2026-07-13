import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
   plugins: [react(), tailwindcss()],

   resolve: {
      alias: {
         '@': path.resolve(__dirname, './src'),
      },
   },

   build: {
      outDir: 'dist-widget',
      emptyOutDir: true,

      rollupOptions: {
         input: path.resolve(__dirname, 'widget.html'),

         output: {
            entryFileNames: 'ramon-burble.js',
            chunkFileNames: 'ramon-burble.js',
            assetFileNames: (assetInfo) => {
               if (assetInfo.name?.endsWith('.css')) return 'ramon-burble.css';
               return '[name][extname]';
            },
            manualChunks: undefined,
         },
      },
   },
});
