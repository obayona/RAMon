import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';
import fs from 'fs';

function serveFonts(): Plugin {
   return {
      name: 'serve-fonts',
      configureServer(server) {
         const fontsDir = path.resolve(__dirname, './fonts');
         server.middlewares.use((req, res, next) => {
            if (req.url?.endsWith('.woff2')) {
               const filePath = path.join(fontsDir, path.basename(req.url));
               if (fs.existsSync(filePath)) {
                  res.setHeader('Content-Type', 'font/woff2');
                  fs.createReadStream(filePath).pipe(res);
                  return;
               }
            }
            next();
         });
      },
   };
}

export default defineConfig({
   plugins: [react(), tailwindcss(), serveFonts()],
   resolve: {
      alias: {
         '@': path.resolve(__dirname, './src'),
      },
   },
});
