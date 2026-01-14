#!/bin/bash

# V5 Clean Deployment Script
# Usage: sudo ./reset_and_deploy.sh

echo "======================================================="
echo "   WFM-PRO: CLEAN DEPLOYMENT PROTOCOL (V5) initiated"
echo "======================================================="

# 1. STOP & CLEAN
echo "--> 1. Stopping containers and cleaning volumes..."
docker-compose down -v
if [ $? -ne 0 ]; then echo "Error stopping containers"; exit 1; fi

# 2. PULL LATEST CODE
echo "--> 2. Pulling latest code from GitHub..."
git pull origin master
if [ $? -ne 0 ]; then echo "Error pulling code"; exit 1; fi

# 3. BUILD
echo "--> 3. Building Docker images (fresh build)..."
docker-compose build --no-cache
if [ $? -ne 0 ]; then echo "Error building images"; exit 1; fi

# 4. START SERVICES & SSL
echo "--> 4. Starting services and initializing SSL..."
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh
if [ $? -ne 0 ]; then echo "Error starting services"; exit 1; fi

# 5. WAIT FOR DATABASE
echo "--> 5. Waiting for Database to be ready..."
# Simple wait loop
for i in {1..30}; do
    if docker-compose exec web python -c "import django; from django.db import connections; from django.db.utils import OperationalError; django.setup(); c = connections['default']; c.cursor()" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    echo "Waiting for DB... ($i/30)"
    sleep 2
done

# 6. RUN MIGRATIONS
echo "--> 6. Running Database Migrations..."
docker-compose exec web python manage.py migrate_schemas --shared
if [ $? -ne 0 ]; then echo "Error running migrations"; exit 1; fi

# 7. CREATE PUBLIC TENANT
echo "--> 7. Creating Public Tenant (wfm-pro.com)..."
# Inject the domain name environment variable just for this command if not in .env
docker-compose exec -e DOMAIN_NAME=wfm-pro.com web python create_public_tenant.py
if [ $? -ne 0 ]; then echo "Error creating tenant"; exit 1; fi

# 8. CREATE SUPERUSER
echo "--> 8. Creating Admin User..."
echo "Please enter the details for the Super Admin user when prompted:"
docker-compose exec web python manage.py create_tenant_superuser

echo "======================================================="
echo "   DEPLOYMENT COMPLETE! 🚀"
echo "   Visit: https://wfm-pro.com"
echo "======================================================="
