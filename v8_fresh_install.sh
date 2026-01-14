#!/bin/bash

# V8 FRESH INSTALLATION SCRIPT
# WARNING: THIS WILL DELETE ALL DATA AND START FRESH
# USE AT YOUR OWN RISK

echo "======================================================="
echo "   WFM-PRO: V8 FRESH INSTALL (Clean Slate)"
echo "======================================================="

# 1. EXTREME CLEANUP
echo "--> 1. Stopping containers and removing volumes..."
docker-compose down -v --remove-orphans

echo "--> 2. Pruning Docker System (Fixes Build Errors)..."
# This fixes "KeyError: ContainerConfig" by clearing the build cache
docker system prune -a -f

# 2. GIT RESET (Force Match GitHub)
echo "--> 3. Resetting Git state..."
git fetch --all
git reset --hard origin/master
chmod +x *.sh

# 3. FRESH BUILD
echo "--> 4. Building services from scratch..."
docker-compose build --no-cache web worker nginx

# 4. SSL CERTIFICATES
echo "--> 5. Initializing SSL..."
# This script handles cert generation
./init-letsencrypt.sh

# 5. START EVERYTHING
echo "--> 6. Starting Application..."
docker-compose up -d

# 6. WAIT FOR DATABASE
echo "--> 7. Waiting for Database to be ready..."
sleep 15

# 7. INITIALIZE DATA
echo "--> 8. Applying Migrations..."
docker-compose exec -T web python manage.py migrate_schemas --shared

echo "--> 9. Creating Public Tenant..."
docker-compose exec -T web python create_public_tenant.py

echo "--> 10. Creating Subscription Plans..."
docker-compose exec -T web python init_plans.py

echo "======================================================="
echo "   V8 INSTALLATION COMPLETE! ✅"
echo "   System is verified and running."
echo "   Check: https://wfm-pro.com"
echo "======================================================="
