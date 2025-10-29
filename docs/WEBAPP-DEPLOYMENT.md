# YouTube Study Buddy Web App - Deployment Guide

## Overview

This guide covers deploying the complete YouTube Study Buddy web application with FastAPI backend, React frontend, PostgreSQL database, Redis cache, WebSocket server, and multi-Tor proxy setup.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Nginx Reverse Proxy (80/443)                │
│                     (Production Only)                         │
└────────────┬──────────────────────┬──────────────────────────┘
             │                      │
    ┌────────▼────────┐    ┌───────▼──────┐
    │  React Frontend │    │  FastAPI     │
    │  (Vite + React) │    │  Backend     │
    │  Port 5173      │    │  Port 8000   │
    └─────────────────┘    └───┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
    ┌────▼────┐     ┌──────────▼─────┐    ┌────────▼────────┐
    │PostgreSQL│     │ WebSocket      │    │ Celery Worker   │
    │Port 5432 │     │ Port 8001      │    │ (Background)    │
    └──────────┘     └────────┬───────┘    └─────────────────┘
                              │
                     ┌────────▼──────┐
                     │   Redis       │
                     │   Port 6379   │
                     └───────────────┘

    ┌─────────────────────────────────────────────┐
    │   Tor Proxies (5 instances)                 │
    │   9050/9052/9054/9056/9058                  │
    └─────────────────────────────────────────────┘
```

## Quick Start (Development)

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

### 1. Clone and Setup

```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy

# Copy environment template
cp .env.webapp.example .env

# Edit with your credentials
nano .env
```

### 2. Required Environment Variables

Update these in `.env`:

```bash
# Security (REQUIRED)
JWT_SECRET_KEY=your-random-32+ -character-secret
POSTGRES_PASSWORD=strong-database-password
REDIS_PASSWORD=strong-redis-password

# Claude API (REQUIRED)
CLAUDE_API_KEY=your-claude-api-key

# OAuth (At least one required for login)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Stripe (Required for payments)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### 3. Run Setup Script

```bash
./scripts/setup-webapp.sh
```

This will:
- Validate environment variables
- Pull and build Docker images
- Start database and Redis
- Run database migrations
- Start all services
- Display service URLs

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8001

## Manual Setup

If you prefer manual control:

### Build Images

```bash
docker-compose -f docker-compose.webapp.yml build
```

### Start Services

```bash
# Start database services first
docker-compose -f docker-compose.webapp.yml up -d postgres redis

# Wait for database to be ready
docker-compose -f docker-compose.webapp.yml exec postgres pg_isready

# Run migrations
docker-compose -f docker-compose.webapp.yml run --rm backend uv run alembic upgrade head

# Start all services
docker-compose -f docker-compose.webapp.yml up -d
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.webapp.yml logs -f

# Specific service
docker-compose -f docker-compose.webapp.yml logs -f backend
docker-compose -f docker-compose.webapp.yml logs -f frontend
docker-compose -f docker-compose.webapp.yml logs -f worker
```

### Stop Services

```bash
# Stop (preserves data)
docker-compose -f docker-compose.webapp.yml down

# Stop and remove volumes (deletes all data!)
docker-compose -f docker-compose.webapp.yml down -v
```

## OAuth Provider Setup

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/auth/callback/google`
6. Copy Client ID and Secret to `.env`

### GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create new OAuth App
3. Homepage URL: `http://localhost:5173`
4. Callback URL: `http://localhost:8000/auth/callback/github`
5. Copy Client ID and Secret to `.env`

### Discord OAuth

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application
3. Go to OAuth2 settings
4. Add redirect: `http://localhost:8000/auth/callback/discord`
5. Copy Client ID and Secret to `.env`

## Stripe Setup

### Development Mode

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/test/dashboard)
2. Get test API keys from Developers > API keys
3. Copy to `.env`:
   - Secret key: `sk_test_...`
   - Publishable key: `pk_test_...`

### Webhook Setup

For local development with Stripe webhooks:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local backend
stripe listen --forward-to localhost:8000/credits/webhooks/stripe

# Copy the webhook signing secret to .env
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Test Cards

Use these test cards in development:
- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **3D Secure**: 4000 0025 0000 3155

## Database Management

### Run Migrations

```bash
# Upgrade to latest
docker-compose -f docker-compose.webapp.yml run --rm backend uv run alembic upgrade head

# Downgrade one version
docker-compose -f docker-compose.webapp.yml run --rm backend uv run alembic downgrade -1
```

### Create Migration

```bash
docker-compose -f docker-compose.webapp.yml run --rm backend uv run alembic revision --autogenerate -m "description"
```

### Access PostgreSQL

```bash
docker-compose -f docker-compose.webapp.yml exec postgres psql -U ytstudy -d ytstudy
```

### Backup Database

```bash
docker-compose -f docker-compose.webapp.yml exec postgres pg_dump -U ytstudy ytstudy > backup.sql
```

### Restore Database

```bash
docker-compose -f docker-compose.webapp.yml exec -T postgres psql -U ytstudy -d ytstudy < backup.sql
```

## Production Deployment

### 1. Update Environment

Create `.env.production`:

```bash
# Application
DEBUG=false
APP_NAME="YouTube Study Buddy"

# URLs (update for your domain)
API_URL=https://api.yourdomain.com
WS_URL=wss://api.yourdomain.com/ws
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Use strong secrets
JWT_SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 32)
REDIS_PASSWORD=$(openssl rand -hex 32)

# Production Stripe keys
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2. SSL/TLS Setup

Update `docker/nginx.conf` for HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # ... rest of config
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Deploy with Production Profile

```bash
# Start with Nginx reverse proxy
docker-compose -f docker-compose.webapp.yml --profile production up -d
```

### 4. Setup Domain DNS

Point your domain to the server IP:

```
A    yourdomain.com         -> YOUR_SERVER_IP
A    www.yourdomain.com     -> YOUR_SERVER_IP
A    api.yourdomain.com     -> YOUR_SERVER_IP
```

### 5. Setup SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal (cron)
sudo certbot renew --dry-run
```

### 6. Production Checklist

- [ ] Strong passwords for all services
- [ ] HTTPS enabled with valid SSL certificate
- [ ] OAuth redirect URIs updated for production domain
- [ ] Stripe webhook endpoint updated
- [ ] CORS origins configured correctly
- [ ] Database backups scheduled
- [ ] Monitoring and logging enabled
- [ ] Firewall configured (only 80, 443 open)
- [ ] Rate limiting enabled
- [ ] Email notifications configured
- [ ] Sentry or error tracking setup

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:5173

# WebSocket health
curl http://localhost:8001/health
```

### Service Status

```bash
docker-compose -f docker-compose.webapp.yml ps
```

### Resource Usage

```bash
docker stats
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.webapp.yml logs

# Restart services
docker-compose -f docker-compose.webapp.yml restart
```

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.webapp.yml ps postgres

# Check database logs
docker-compose -f docker-compose.webapp.yml logs postgres

# Test connection
docker-compose -f docker-compose.webapp.yml exec postgres pg_isready -U ytstudy
```

### Redis Connection Errors

```bash
# Check if Redis is running
docker-compose -f docker-compose.webapp.yml ps redis

# Test connection
docker-compose -f docker-compose.webapp.yml exec redis redis-cli -a ${REDIS_PASSWORD} ping
```

### Port Conflicts

```bash
# Check what's using a port
lsof -i :8000
lsof -i :5173

# Kill process using port
kill -9 $(lsof -t -i:8000)
```

### Clear Everything and Start Fresh

```bash
# Stop and remove everything
docker-compose -f docker-compose.webapp.yml down -v

# Remove images
docker-compose -f docker-compose.webapp.yml rm -f

# Rebuild and start
./scripts/setup-webapp.sh
```

## Scaling

### Horizontal Scaling

For high traffic, you can scale services:

```bash
# Scale backend replicas
docker-compose -f docker-compose.webapp.yml up -d --scale backend=3

# Scale worker replicas
docker-compose -f docker-compose.webapp.yml up -d --scale worker=5
```

### Load Balancing

Update Nginx config for load balancing:

```nginx
upstream backend {
    least_conn;
    server backend-1:8000;
    server backend-2:8000;
    server backend-3:8000;
}
```

## Maintenance

### Updating Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.webapp.yml build
docker-compose -f docker-compose.webapp.yml up -d

# Run new migrations
docker-compose -f docker-compose.webapp.yml run --rm backend uv run alembic upgrade head
```

### Database Cleanup

```bash
# Remove old completed jobs
docker-compose -f docker-compose.webapp.yml exec backend uv run python -c "
from api.jobs.cleanup import cleanup_old_jobs
cleanup_old_jobs(days=30)
"
```

### Log Rotation

Add to `/etc/logrotate.d/docker-compose`:

```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
```

## Performance Tuning

### PostgreSQL

Update `docker-compose.webapp.yml`:

```yaml
postgres:
  command: postgres -c max_connections=200 -c shared_buffers=256MB
```

### Redis

```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Worker Concurrency

```yaml
worker:
  command: celery -A api.jobs.worker worker --concurrency=10
```

## Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose.webapp.yml logs`
2. Review this guide's troubleshooting section
3. Check the API docs: http://localhost:8000/docs
4. Open an issue on GitHub

---

**Last Updated**: 2025-10-29
**Version**: 1.0.0
