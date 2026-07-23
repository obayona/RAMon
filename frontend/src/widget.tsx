import { createRoot } from 'react-dom/client';
import RamonWidget from './widget/RamonWidget';
import { RamonProvider } from './context/RamonContext';
import { getConfig } from './widget/getConfig';
import styles from './widget.css?inline';

const config = getConfig();
console.log(styles);

// Create host element
const hostElement = document.createElement('div');
hostElement.id = 'ramon-widget-host';
document.body.appendChild(hostElement);

// Create shadow root for style isolation
const shadowRoot = hostElement.attachShadow({ mode: 'open' });

// Inject styles into shadow DOM
const styleElement = document.createElement('style');
let shadowStyles = styles.replaceAll(':root', ':host');
shadowStyles = shadowStyles.replaceAll('.dark', ':host(.dark)');

styleElement.textContent = shadowStyles;
shadowRoot.appendChild(styleElement);

// Create root element inside shadow DOM
const rootElement = document.createElement('div');
rootElement.id = 'ramon-widget';
shadowRoot.appendChild(rootElement);

createRoot(rootElement).render(
   <RamonProvider config={config}>
      <RamonWidget />
   </RamonProvider>,
);
