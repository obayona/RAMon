import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js';
import path from 'path';

export default defineConfig({
   plugins: [react(), tailwindcss(), cssInjectedByJsPlugin()],

   resolve: {
      alias: {
         '@': path.resolve(__dirname, './src'),
      },
   },

   build: {
      lib: {
         entry: path.resolve(__dirname, 'src/widget.tsx'),
         name: 'RamonWidget',
         formats: ['iife'],
         fileName: () => 'ramon',
      },

      cssCodeSplit: false,

      emptyOutDir: true,

      rollupOptions: {
         output: {
            inlineDynamicImports: true,
         },
      },
   },
});
