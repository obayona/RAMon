import { createRoot } from 'react-dom/client';

import RamonWidget from './widget/RamonWidget';

import { RamonProvider } from './context/RamonContext';

import { getConfig } from './widget/getConfig';

const config = getConfig();

const rootElement = document.createElement('div');

rootElement.id = 'ramon-widget';

document.body.appendChild(rootElement);

createRoot(rootElement).render(
   <RamonProvider config={config}>
      <RamonWidget />
   </RamonProvider>,
);
