#!/bin/bash
# Initialize SSL certificates for production deployment
# Usage: ./scripts/init-ssl.sh

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DOMAIN" ]; then
    echo "Error: DOMAIN is not set in .env file"
    exit 1
fi

if [ -z "$CERTBOT_EMAIL" ]; then
    echo "Error: CERTBOT_EMAIL is not set in .env file"
    exit 1
fi

echo "=== RAMon SSL Certificate Setup ==="
echo "Domain: $DOMAIN"
echo "Email: $CERTBOT_EMAIL"
echo ""

# Create required directories
mkdir -p certbot/www certbot/conf

# Step 1: Start services with HTTP-only nginx config
echo "Step 1: Starting services with HTTP-only configuration..."
cp nginx/conf.d/default.conf.nossl nginx/conf.d/default.conf
docker compose -f docker-compose.prod.yml up -d postgres api nginx

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Step 2: Request SSL certificate
echo ""
echo "Step 2: Requesting SSL certificate from Let's Encrypt..."
docker compose -f docker-compose.prod.yml run --rm \
  --entrypoint certbot \
  certbot \
  certonly \
  --webroot \
  -w /var/www/certbot \
  --email "$CERTBOT_EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

# Step 3: Generate nginx config with SSL
echo ""
echo "Step 3: Generating nginx configuration with SSL..."
sed "s/\${DOMAIN}/$DOMAIN/g" nginx/conf.d/default.conf.template > nginx/conf.d/default.conf

# Step 4: Reload nginx with SSL configuration
echo ""
echo "Step 4: Reloading nginx with SSL configuration..."
docker compose -f docker-compose.prod.yml restart nginx

echo ""
echo "=== SSL Setup Complete ==="
echo "Your site should now be accessible at: https://$DOMAIN"
echo ""
echo "To enable automatic certificate renewal, run:"
echo "  docker compose -f docker-compose.prod.yml --profile certbot up -d certbot"
