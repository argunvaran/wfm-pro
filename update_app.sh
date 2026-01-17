#!/bin/bash

# V7 Safe Update Script
# Updates code, DB, and static files safely

echo "======================================================="
echo "   WFM-PRO: SAFE UPDATE PROTOCOL (V7)"
echo "======================================================="

# 1. Pull Code
echo "--> 1. Pulling latest changes..."
git pull origin master

# 2. Rebuild Container (Safe)
# This respects the existing DB volume, so data is safe.
echo "--> 2. Rebuilding services..."
sudo docker-compose up -d --build web worker

# 3. Apply Migrations
# Standard migrate covering both public and tenants (if configured)
echo "--> 3. Applying Database Migrations..."
sudo docker-compose exec web python manage.py migrate

# 4. Collect Static Files
# Crucial for CSS/JS updates to be visible via Nginx
echo "--> 4. Collecting Static Files..."
sudo docker-compose exec web python manage.py collectstatic --noinput

# 5. Update Plans (Optional but good for safety)
echo "--> 5. Updating Subscription Plans..."
sudo docker-compose exec web python init_plans.py

# 6. Restart Worker to pick up new code
echo "--> 6. Restarting Worker..."
sudo docker-compose restart worker

echo "======================================================="
echo "   UPDATE COMPLETE! ✅"
echo "   Your data and SSL certs were NOT touched."
echo "======================================================="
