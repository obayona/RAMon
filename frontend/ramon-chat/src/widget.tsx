import { createRoot } from 'react-dom/client';

import RamonWidget from './widget/RamonWidget';

import { RamonProvider } from './context/RamonContext';

import { getConfig } from './widget/getConfig';
import './App.css';

function loadWidgetCSS() {
   const currentScript = document.currentScript as HTMLScriptElement | null;

   if (!currentScript) return;

   const cssUrl = currentScript.src.replace(/\.js$/, '.css');

   if (document.querySelector(`link[href="${cssUrl}"]`)) {
      return;
   }

   const link = document.createElement('link');

   link.rel = 'stylesheet';

   link.href = cssUrl;

   document.head.appendChild(link);
}

loadWidgetCSS();

const config = getConfig();

const rootElement = document.createElement('div');

rootElement.id = 'ramon-widget';

document.body.appendChild(rootElement);

createRoot(rootElement).render(
   <RamonProvider config={config}>
      <RamonWidget />
   </RamonProvider>,
);
