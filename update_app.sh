#!/bin/bash

# V6 Safe Update Script
# Updates code and DB without destroying containers/SSL

echo "======================================================="
echo "   WFM-PRO: SAFE UPDATE PROTOCOL (V6)"
echo "======================================================="

# 1. Pull Code
echo "--> 1. Pulling latest changes..."
git pull origin master

# 2. Update Python Dependencies (if any)
# We use --no-deps to avoid reinstalling everything, just check for new ones
# But usually we need to rebuild if requirements changed.
# For this V6 change, we added logical changes.
# If we need to rebuild: docker-compose build web worker
# Let's assume safely we might need to rebuild if requirements changed, but 
# 'docker-compose up -d --build' does that safely without losing volumes.
echo "--> 2. Rebuilding services (Safe mode)..."
docker-compose up -d --build web worker celery

# 3. Create Migrations (Since we added fields)
echo "--> 3. Creating Database Migrations..."
docker-compose exec web python manage.py makemigrations

# 4. Migrate DB
echo "--> 4. Applying Migrations..."
docker-compose exec web python manage.py migrate_schemas --shared

# 5. Update Plans
echo "--> 5. Updating Subscription Plans..."
docker-compose exec web python init_plans.py

# 6. Restart to ensure all code is loaded
echo "--> 6. Restarting Services..."
docker-compose restart web worker

echo "======================================================="
echo "   UPDATE COMPLETE! ✅"
echo "   SSL Certificates: PROTECTED (Not touched)"
echo "======================================================="
