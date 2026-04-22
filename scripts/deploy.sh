#!/bin/bash
# FleetOps Production Deployment Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/fleetops"
BACKUP_DIR="/backups/fleetops"
LOG_FILE="/var/log/fleetops-deploy.log"

log() {
    echo -e "${GREEN}[$(date +%Y-%m-%d\ %H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +%Y-%m-%d\ %H:%M:%S)] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +%Y-%m-%d\ %H:%M:%S)] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root or with sudo"
fi

log "Starting FleetOps deployment..."

# Create directories
log "Creating directories..."
mkdir -p "$DEPLOY_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p /var/log

# Install dependencies
log "Installing system dependencies..."
apt-get update
apt-get install -y docker.io docker-compose git curl nginx certbot python3-certbot-nginx

# Start Docker
systemctl enable docker
systemctl start docker

# Clone or update repository
if [ -d "$DEPLOY_DIR/.git" ]; then
    log "Updating existing installation..."
    cd "$DEPLOY_DIR"
    git pull origin main
else
    log "Cloning repository..."
    cd /opt
    git clone https://github.com/LunarPerovskite/FleetOps.git fleetops
fi

# Check environment file
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    warn "No .env file found. Copying from example..."
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
    warn "Please edit $DEPLOY_DIR/.env with your configuration"
fi

# Build and start
log "Building Docker containers..."
cd "$DEPLOY_DIR"
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services
log "Waiting for services to start..."
sleep 30

# Health check
log "Running health checks..."
if curl -sf http://localhost:8000/health > /dev/null; then
    log "✅ Backend is healthy"
else
    error "Backend health check failed"
fi

if curl -sf http://localhost:3000 > /dev/null; then
    log "✅ Frontend is healthy"
else
    warn "Frontend health check failed (may need more time)"
fi

# Setup SSL with Certbot (if domain is configured)
if grep -q "DOMAIN=" "$DEPLOY_DIR/.env" 2>/dev/null; then
    DOMAIN=$(grep "DOMAIN=" "$DEPLOY_DIR/.env" | cut -d'=' -f2)
    if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
        log "Setting up SSL for $DOMAIN..."
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN 2>/dev/null || warn "SSL setup failed, you may need to run manually"
    fi
fi

# Setup backup cron job
if ! crontab -l 2>/dev/null | grep -q "fleetops_backup"; then
    log "Setting up automated backups..."
    (crontab -l 2>/dev/null; echo "0 2 * * * $DEPLOY_DIR/scripts/backup.sh >> /var/log/fleetops-backup.log 2>&1") | crontab -
fi

# Setup log rotation
cat > /etc/logrotate.d/fleetops <<EOF
/var/log/fleetops*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

log "✅ Deployment complete!"
log ""
log "FleetOps is now running at:"
log "  - Frontend: http://localhost:3000"
log "  - API: http://localhost:8000"
log "  - Health: http://localhost:8000/health"
log ""
log "View logs: docker-compose -f docker-compose.prod.yml logs -f"
log "Stop: docker-compose -f docker-compose.prod.yml down"
