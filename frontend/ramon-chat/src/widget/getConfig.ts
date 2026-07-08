import type { RamonConfig } from '@/types/config';

export function getConfig(): RamonConfig {
   const element = document.getElementById('ramon-config');

   if (!element) {
      throw new Error('No existe ramon-config');
   }

   return JSON.parse(element.textContent || '{}');
}
