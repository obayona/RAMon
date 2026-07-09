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

      rollupOptions: {
         input: path.resolve(__dirname, 'widget.html'),

         output: {
            entryFileNames: 'ramon.js',
            chunkFileNames: 'ramon.js',
            assetFileNames: '[name][extname]',
            manualChunks: undefined,
         },
      },
   },
});
