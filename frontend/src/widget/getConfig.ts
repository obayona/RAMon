import type { RamonConfig } from '@/types/config';

export function getConfig(): RamonConfig {
   const config = (window as unknown as Record<string, unknown>)
      .__RAMON_CONFIG__ as RamonConfig | undefined;

   if (!config) {
      throw new Error(
         'RAMon config not found. Ensure the loader (ramon.js) is loaded first.',
      );
   }

   return config;
}
