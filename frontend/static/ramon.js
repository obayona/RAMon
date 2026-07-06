/**
 * RAMon Chat Widget
 * 
 * A chat bubble widget that can be embedded on any website.
 * Reads authentication token from a <script id="ramon-config"> element.
 */
(function() {
  'use strict';

  // Configuration
  const CONFIG_ELEMENT_ID = 'ramon-config';
  
  /**
   * Read the JWT token from the configuration script element.
   * @returns {string|null} The token or null if not found.
   */
  function getConfig() {
    const configEl = document.getElementById(CONFIG_ELEMENT_ID);
    if (!configEl) {
      console.warn('RAMon: Config element not found');
      return null;
    }
    
    try {
      const config = JSON.parse(configEl.textContent);
      return config;
    } catch (e) {
      console.error('RAMon: Failed to parse config:', e);
      return null;
    }
  }

  /**
   * Inject the chat bubble styles into the document.
   */
  function injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      #ramon-bubble {
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
        z-index: 9999;
        border: none;
        outline: none;
      }
      
      #ramon-bubble:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
      }
      
      #ramon-bubble:active {
        transform: scale(0.95);
      }
      
      #ramon-bubble svg {
        width: 28px;
        height: 28px;
        fill: white;
      }
      
      #ramon-bubble .badge {
        position: absolute;
        top: -2px;
        right: -2px;
        width: 18px;
        height: 18px;
        background: #ef4444;
        border-radius: 50%;
        font-size: 11px;
        font-weight: 600;
        color: white;
        display: none;
        align-items: center;
        justify-content: center;
        font-family: system-ui, -apple-system, sans-serif;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Create and render the chat bubble button.
   * @param {string} token - The JWT token for authentication.
   */
  function renderBubble(token) {
    const bubble = document.createElement('button');
    bubble.id = 'ramon-bubble';
    bubble.setAttribute('aria-label', 'Open chat assistant');
    bubble.innerHTML = `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      </svg>
      <span class="badge">1</span>
    `;
    
    bubble.addEventListener('click', function() {
      console.log('RAMon: Chat bubble clicked');
      console.log('RAMon: Token available:', !!token);
      // TODO: Implement chat window opening
    });
    
    document.body.appendChild(bubble);
  }

  /**
   * Initialize the RAMon chat widget.
   */
  function init() {
    const {token, api_url, product_id} = getConfig();
    console.log(token, api_url, product_id)
    
    if (!token) {
      console.error('RAMon: No token found, widget will not initialize');
      return;
    }
    
    console.log('RAMon: Initializing chat widget');
    
    injectStyles();
    renderBubble(token);
    
    console.log('RAMon: Widget ready');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
