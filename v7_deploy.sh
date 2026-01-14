#!/bin/bash

# V7 DEFINITIVE DEPLOYMENT SCRIPT
# This script forces a clean state to resolve "No such service" and git conflict errors.

echo "======================================================="
echo "   WFM-PRO: V7 DEFINITIVE DEPLOYMENT"
echo "======================================================="

# 1. FORCE GIT RESET (Fixes the messy state)
echo "--> 1. Resetting Git state (Force)..."
git fetch --all
git reset --hard origin/master
if [ $? -ne 0 ]; then echo "Git reset failed"; exit 1; fi

# 2. PULL LATEST (Just to be sure)
echo "--> 2. Pulling latest code..."
git pull origin master

# 3. FIX PERMISSIONS
chmod +x *.sh

# 4. REBUILD SPECIFIC SERVICES (Web & Worker)
# We explicitly name 'worker' to avoid the 'celery' error
echo "--> 3. Rebuilding Web and Worker..."
docker-compose up -d --build web worker nginx
if [ $? -ne 0 ]; then echo "Build failed"; exit 1; fi

# 5. RUN MIGRATIONS
echo "--> 4. Running Migrations..."
docker-compose exec -T web python manage.py migrate_schemas --shared

# 6. UPDATE PLANS
echo "--> 5. Updating Plans..."
docker-compose exec -T web python init_plans.py

# 7. RESTART EVERYTHING (Safe Restart)
echo "--> 6. Restarting Services..."
docker-compose restart web worker nginx

echo "======================================================="
echo "   V7 DEPLOYMENT SUCCESSFUL! 🚀"
echo "   Please check https://wfm-pro.com"
echo "======================================================="
