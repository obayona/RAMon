# RAMon Production Deployment Guide

This guide covers deploying RAMon to a production server with Docker, nginx, and SSL certificates.

## Prerequisites

- A server with Docker and Docker Compose installed
- A domain name pointing to your server's IP address
- Ports 80 and 443 open in your firewall

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd ramon

# 2. Copy and configure environment variables
cp .env.example .env
nano .env  # Edit with your values

# 3. Initialize SSL and start services
./scripts/init-ssl.sh

# 4. Load product fixtures (optional)
docker compose -f docker-compose.prod.yml run --rm fixtures-load
```

## Step-by-Step Deployment

### 1. Configure Environment Variables

Copy the example file and edit it:

```bash
cp .env.example .env
```

Required variables for production:

```bash
# Database (use strong passwords!)
DB_PASSWORD='your-secure-password-here'  # Generate: openssl rand -base64 24

# API Keys
OPENAI_API_KEY='sk-...'
TAVILY_API_KEY='tvly-...'

# Auth
APP_KEY='your-jwt-secret-key'  # Generate: openssl rand -base64 32

# Production
DOMAIN='api.yourdomain.com'
CERTBOT_EMAIL='admin@yourdomain.com'
```

### 2. Initial Deployment (Without SSL)

For the first deployment, start services with HTTP-only configuration:

```bash
# Create required directories
mkdir -p certbot/www certbot/conf

# Use the HTTP-only nginx config initially
cp nginx/conf.d/default.conf.nossl nginx/conf.d/default.conf

# Build and start services
docker compose -f docker-compose.prod.yml up -d --build
```

Verify services are running:

```bash
docker compose -f docker-compose.prod.yml ps
curl http://your-server-ip/health
```

### 3. Obtain SSL Certificate

Once your domain DNS is pointing to the server:

```bash
# Request certificate from Let's Encrypt
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d your-domain.com
```

### 4. Enable SSL in nginx

Generate the SSL-enabled nginx configuration:

```bash
# Replace DOMAIN placeholder with your actual domain
sed "s/\${DOMAIN}/your-domain.com/g" \
    nginx/conf.d/default.conf.template > nginx/conf.d/default.conf

# Restart nginx to apply SSL configuration
docker compose -f docker-compose.prod.yml restart nginx
```

### 5. Enable Automatic Certificate Renewal

Start the certbot renewal service:

```bash
docker compose -f docker-compose.prod.yml --profile certbot up -d certbot
```

### 6. Load Product Data (Optional)

```bash
docker compose -f docker-compose.prod.yml run --rm fixtures-load
```

## Using the init-ssl.sh Script

For convenience, all SSL setup steps are automated in the init script:

```bash
# Make sure DOMAIN and CERTBOT_EMAIL are set in .env
./scripts/init-ssl.sh
```

This script will:
1. Start services with HTTP-only config
2. Request SSL certificate from Let's Encrypt
3. Generate SSL-enabled nginx config
4. Restart nginx with SSL

## Managing the Deployment

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart api
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

### Database Backup

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec postgres \
    pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U $DB_USER $DB_NAME
```

### Stop Services

```bash
# Stop all services (keeps data)
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (DESTROYS DATA)
docker compose -f docker-compose.prod.yml down -v
```

## SSL Certificate Renewal

Certificates are automatically renewed by the certbot container. To manually renew:

```bash
docker compose -f docker-compose.prod.yml run --rm certbot renew
docker compose -f docker-compose.prod.yml restart nginx
```

## Troubleshooting

### Check Service Health

```bash
# API health check
curl https://your-domain.com/health

# View service status
docker compose -f docker-compose.prod.yml ps

# Check container logs
docker compose -f docker-compose.prod.yml logs api --tail=100
```

### SSL Certificate Issues

```bash
# Check certificate status
docker compose -f docker-compose.prod.yml run --rm certbot certificates

# Test certificate renewal (dry run)
docker compose -f docker-compose.prod.yml run --rm certbot renew --dry-run
```

### Database Connection Issues

```bash
# Check postgres is healthy
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U $DB_USER

# Connect to database
docker compose -f docker-compose.prod.yml exec postgres psql -U $DB_USER $DB_NAME
```

### Nginx Configuration Test

```bash
# Test nginx config syntax
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx config without restart
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

## Security Checklist

- [ ] Strong database password (use `openssl rand -base64 24`)
- [ ] Strong APP_KEY for JWT (use `openssl rand -base64 32`)
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Firewall configured (only ports 80, 443, and SSH open)
- [ ] Regular backups configured
- [ ] Log monitoring set up

## Architecture

```
                    ┌─────────────┐
                    │   Internet  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   nginx     │ :80, :443
                    │  (reverse   │
                    │   proxy)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │     API     │ :8000 (internal)
                    │  (FastAPI + │
                    │  gunicorn)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL │ :5432 (internal)
                    │  + pgvector │
                    └─────────────┘
```

## File Structure

```
.
├── docker-compose.prod.yml    # Production compose file
├── backend/
│   ├── Dockerfile.prod        # Multi-stage production Dockerfile
│   └── ...
├── nginx/
│   ├── nginx.conf             # Main nginx config
│   └── conf.d/
│       ├── default.conf.template  # SSL config template
│       └── default.conf.nossl     # Initial HTTP-only config
├── certbot/
│   ├── www/                   # ACME challenge files
│   └── conf/                  # SSL certificates
└── scripts/
    └── init-ssl.sh            # SSL initialization script
```
