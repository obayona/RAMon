# RAMon Chat Frontend

Embeddable AI chat widget. Ships JS, CSS, and font assets for injection into any website.

## Quick Start

```bash
pnpm install
pnpm dev      # Development with HMR
```

Open http://localhost:3000

## Structure

```
frontend/
├── server.js              # Express server (JWT + Vite middleware)
├── src/
│   ├── loader.js          # Production loader (plain JS)
│   ├── widget.tsx         # Widget entry point
│   ├── widget/            # FloatingButton, ChatWindow, etc.
│   ├── components/        # Chat UI components
│   ├── context/           # RamonContext
│   ├── hooks/             # useChat
│   ├── services/          # WebSocket, history
│   └── types/             # TypeScript types
├── fonts/                 # Geist woff2 files
├── widget.html            # Build entry point
├── vite.config.ts         # Dev config
├── vite.widget.config.ts  # Production build config
└── dist-widget/           # Built output
    ├── ramon.js           # Loader
    ├── ramon-burble.js    # Widget (CSS inlined)
    └── *.woff2            # Fonts
```

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Development server with HMR + JWT generation |
| `pnpm build` | Build production assets to `dist-widget/` |
| `pnpm start` | Serve production assets |
| `pnpm lint` | Run ESLint |

## Development

```bash
pnpm dev
```

Starts a single server that:
- Generates JWT tokens for authentication
- Serves widget source via Vite (unminified, source maps)
- Hot-reloads on code changes

This server is a fake e-commerce website that injects the chatbot widget

## Production

```bash
pnpm build
pnpm start
```

## Embedding on any website

```html
<script>
  window.__RAMON_CONFIG__ = {
    token: "[JWT_TOKEN]",
    productId: "230670",
    apiUrl: "https://api.ramon.ai"
  };
</script>
<script src="https://cdn.example.com/ramon.js"></script>
```

The loader:
1. Loads `ramon-burble.js` (CSS is inlined)
2. Widget reads config from `window.__RAMON_CONFIG__`
3. Widget mounts inside Shadow DOM (styles isolated from host page)

## Environment Variables

Defined on `.env.example`