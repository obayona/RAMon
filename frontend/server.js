const express = require('express');
const jwt = require('jsonwebtoken');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

const APP_KEY = process.env.APP_KEY;
if (!APP_KEY) {
  console.error('APP_KEY environment variable is required');
  process.exit(1);
}

// Read the HTML template once at startup
const indexTemplate = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf-8');

/**
 * Generate a JWT token with 24-hour expiration
 */
function generateToken() {
  const payload = {
    iat: Math.floor(Date.now() / 1000),
  };
  return jwt.sign(payload, APP_KEY, { expiresIn: '24h' });
}

// Serve static files (for ramon.js)
app.use('/static', express.static(path.join(__dirname, 'static')));

// Main route - inject JWT into HTML
app.get('/', (req, res) => {
  const token = generateToken();
  const html = indexTemplate.replace('[TOKEN]', token);
  res.type('html').send(html);
});

app.listen(PORT, () => {
  console.log(`Frontend demo server running at http://localhost:${PORT}`);
});
