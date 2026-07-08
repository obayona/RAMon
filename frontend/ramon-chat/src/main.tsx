import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import { App } from './App.tsx';
import { RamonProvider } from './context/RamonContext.tsx';

createRoot(document.getElementById('root')!).render(
   <StrictMode>
      <RamonProvider
         config={{
            apiUrl: 'http://localhost:8080',
            token: '',
            productId: '230670',
         }}
      >
         <App />
      </RamonProvider>
   </StrictMode>,
);
