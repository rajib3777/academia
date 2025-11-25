#!/bin/bash
set -e

echo "Deploying the application..."

# Pull the latest changes from the repository
git pull origin main
echo "Pulled latest changes."

# Activate Virtual Environment
source venv/bin/activate
echo "Activated virtual environment."

# Install any new dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --no-input

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Deactivate Virtual Environment
deactivate
echo "Deactivated virtual environment."

# Reloading Application so new changes could reflect on website
pushd classmate
touch wsgi.py
popd
echo "Reloaded application."

# Restart the application services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
echo "Deployment completed successfully."