import type { RamonConfig } from '@/types/config';
import { createContext, useContext } from 'react';

const RamonContext = createContext<RamonConfig | null>(null);

interface Props {
   config: RamonConfig;
   children: React.ReactNode;
}

export function RamonProvider({ config, children }: Props) {
   return (
      <RamonContext.Provider value={config}>{children}</RamonContext.Provider>
   );
}

export function useRamonConfig() {
   const config = useContext(RamonContext);

   if (!config) {
      throw new Error('RamonProvider no encontrado');
   }

   return config;
}
