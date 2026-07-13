const express = require('express');
const jwt = require('jsonwebtoken');
const path = require('path');
require('dotenv').config();

const PORT = process.env.PORT || 3000;
const APP_KEY = process.env.APP_KEY;
const isDev = process.argv.includes('--dev');

if (!APP_KEY) {
  console.error('APP_KEY environment variable is required');
  process.exit(1);
}

function generateToken() {
  const payload = { iat: Math.floor(Date.now() / 1000) };
  return jwt.sign(payload, APP_KEY, { expiresIn: '24h' });
}

function renderHTML(token, scriptTag) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TechStore - Computer Hardware</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; color: #1e293b; }
    header { background: #1e293b; color: white; padding: 1rem 2rem; }
    header h1 { font-size: 1.5rem; }
    nav { display: flex; gap: 1.5rem; margin-top: 0.5rem; }
    nav a { color: #94a3b8; text-decoration: none; font-size: 0.9rem; }
    nav a:hover { color: white; }
    main { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
    .hero { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 3rem 2rem; border-radius: 12px; margin-bottom: 2rem; }
    .hero h2 { font-size: 2rem; margin-bottom: 0.5rem; }
    .hero p { opacity: 0.9; }
    .products { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; }
    .product { background: white; border-radius: 10px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .product img { width: 100%; height: 150px; object-fit: contain; background: #f1f5f9; border-radius: 8px; margin-bottom: 1rem; }
    .product h3 { font-size: 1rem; margin-bottom: 0.5rem; }
    .product .price { color: #059669; font-weight: 600; font-size: 1.25rem; }
    .product .specs { color: #64748b; font-size: 0.85rem; margin: 0.5rem 0; }
    .product button { width: 100%; background: #3b82f6; color: white; border: none; padding: 0.75rem; border-radius: 6px; cursor: pointer; font-weight: 500; margin-top: 1rem; }
    .product button:hover { background: #2563eb; }
    footer { text-align: center; padding: 2rem; color: #64748b; font-size: 0.85rem; }
  </style>
</head>
<body>
  <header>
    <h1>TechStore</h1>
    <nav>
      <a href="#">Home</a>
      <a href="#">CPUs</a>
      <a href="#">GPUs</a>
      <a href="#">RAM</a>
      <a href="#">Storage</a>
    </nav>
  </header>

  <main>
    <div class="hero">
      <h2>Build Your Dream PC</h2>
      <p>Find the best hardware components for your needs. Chat with our AI assistant for recommendations!</p>
    </div>

    <div class="products">
      <div class="product">
        <img src="https://placehold.co/300x150/f1f5f9/64748b?text=CPU" alt="CPU">
        <h3>AMD Ryzen 7 7800X3D</h3>
        <div class="specs">8 Cores, 16 Threads, 4.2GHz Base</div>
        <div class="price">$449.99</div>
        <button>Add to Cart</button>
      </div>
      <div class="product">
        <img src="https://placehold.co/300x150/f1f5f9/64748b?text=GPU" alt="GPU">
        <h3>NVIDIA RTX 4070 Super</h3>
        <div class="specs">12GB GDDR6X, 7168 CUDA Cores</div>
        <div class="price">$599.99</div>
        <button>Add to Cart</button>
      </div>
      <div class="product">
        <img src="https://placehold.co/300x150/f1f5f9/64748b?text=RAM" alt="RAM">
        <h3>Corsair Vengeance DDR5</h3>
        <div class="specs">32GB (2x16GB), 6000MHz, CL36</div>
        <div class="price">$129.99</div>
        <button>Add to Cart</button>
      </div>
      <div class="product">
        <img src="https://placehold.co/300x150/f1f5f9/64748b?text=SSD" alt="SSD">
        <h3>Samsung 990 Pro NVMe</h3>
        <div class="specs">2TB, 7450MB/s Read, PCIe 4.0</div>
        <div class="price">$179.99</div>
        <button>Add to Cart</button>
      </div>
    </div>
  </main>

  <footer>
    <p>&copy; 2024 TechStore - Demo E-commerce Site</p>
  </footer>

  <script>
    window.__RAMON_CONFIG__ = {
      token: "${token}",
      productId: "230670",
      apiUrl: "http://localhost:8080"
    };
  </script>
  ${scriptTag}
</body>
</html>`;
}

async function startDev() {
  const { createServer } = await import('vite');
  const app = express();

  const vite = await createServer({
    root: __dirname,
    server: { middlewareMode: true },
  });

  // Handle root route BEFORE Vite middleware
  app.get('/', async (req, res) => {
    const token = generateToken();
    let html = renderHTML(token, '<script type="module" src="/src/widget.tsx"></script>');
    // Transform HTML to inject Vite's HMR preamble
    html = await vite.transformIndexHtml(req.url, html);
    res.type('html').send(html);
  });

  app.use(vite.middlewares);

  app.listen(PORT, () => {
    console.log(`Dev server (HMR enabled) at http://localhost:${PORT}`);
  });
}

function startProd() {
  const app = express();

  app.use('/assets', express.static(path.join(__dirname, 'dist-widget')));

  app.get('/', (req, res) => {
    const token = generateToken();
    const html = renderHTML(token, '<script src="/assets/ramon.js"></script>');
    res.type('html').send(html);
  });

  app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
  });
}

if (isDev) {
  startDev();
} else {
  startProd();
}
