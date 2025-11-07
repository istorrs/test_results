# Ubuntu Server Deployment Guide

This guide provides step-by-step instructions for deploying the Test Results Database on an Ubuntu server.

## Prerequisites

- Ubuntu 20.04 LTS or later
- Sudo access
- At least 2GB RAM
- 20GB available disk space

## Installation Steps

### 1. Install Docker and Docker Compose

```bash
# Update package index
sudo apt-get update

# Install required packages
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### 2. Clone the Repository

```bash
cd /opt
sudo git clone https://github.com/istorrs/test_results.git
cd test_results
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate a secure secret key
openssl rand -hex 32

# Edit the .env file
nano .env
```

**Important environment variables to set:**

```bash
# MongoDB
MONGODB_URL=mongodb://mongodb:27017/test_results
MONGODB_DB_NAME=test_results

# Security - USE THE GENERATED KEY!
SECRET_KEY=your-secure-random-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Test Results Database
BACKEND_CORS_ORIGINS=["http://your-domain.com", "http://localhost:3000"]

# Frontend URL
FRONTEND_URL=http://your-domain.com
```

### 4. Start the Application

```bash
# For development/testing
docker compose up -d

# For production
docker compose -f docker-compose.prod.yml up -d
```

### 5. Verify Installation

```bash
# Check running containers
docker compose ps

# Check logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mongodb

# Test the API
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 6. Access the Application

- **API Documentation**: http://your-server-ip:8000/docs
- **Frontend**: http://your-server-ip:3000

## Production Setup with Nginx Reverse Proxy

### 1. Install Nginx

```bash
sudo apt-get update
sudo apt-get install -y nginx
```

### 2. Configure Nginx

Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/test-results
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    client_max_body_size 20M;
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/test-results /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

## Firewall Configuration

```bash
# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

## Maintenance

### View Logs

```bash
# Backend logs
docker compose logs -f backend

# Frontend logs
docker compose logs -f frontend

# MongoDB logs
docker compose logs -f mongodb

# All logs
docker compose logs -f
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart backend
```

### Update Application

```bash
cd /opt/test_results
git pull origin main
docker compose down
docker compose build
docker compose up -d
```

### Backup MongoDB Data

```bash
# Create backup directory
mkdir -p /opt/backups/mongodb

# Backup database
docker exec test_results_mongodb mongodump --out /backup
docker cp test_results_mongodb:/backup /opt/backups/mongodb/$(date +%Y%m%d_%H%M%S)
```

### Restore MongoDB Data

```bash
docker cp /opt/backups/mongodb/BACKUP_DATE test_results_mongodb:/backup
docker exec test_results_mongodb mongorestore /backup
```

## Monitoring

### Check Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# MongoDB stats
docker exec test_results_mongodb mongo --eval "db.stats()"
```

### Set Up Auto-Start on Boot

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Services will auto-start with restart: always in docker-compose.prod.yml
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. MongoDB not accessible - check network
# 2. Environment variables not set
# 3. Port 8000 already in use
```

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
docker compose ps mongodb

# Check MongoDB logs
docker compose logs mongodb

# Test connection
docker exec -it test_results_mongodb mongosh
```

### Disk Space Issues

```bash
# Clean up Docker
docker system prune -a

# Remove old MongoDB data (be careful!)
docker volume ls
docker volume rm test_results_mongodb_data
```

## Security Recommendations

1. **Change default SECRET_KEY** - Use a strong, random key
2. **Use HTTPS** - Set up SSL certificates
3. **Firewall** - Only expose necessary ports
4. **MongoDB** - Don't expose port 27017 publicly
5. **API Keys** - Rotate regularly
6. **Updates** - Keep system and Docker images updated
7. **Backups** - Regular database backups
8. **Monitoring** - Set up logging and monitoring

## Production Checklist

- [ ] Secure SECRET_KEY set in .env
- [ ] CORS origins configured correctly
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] MongoDB not exposed publicly
- [ ] Regular backups scheduled
- [ ] Monitoring set up
- [ ] Log rotation configured
- [ ] Auto-start on boot enabled
- [ ] DNS configured for domain

## Support

For issues and questions, please open a GitHub issue at:
https://github.com/istorrs/test_results/issues
