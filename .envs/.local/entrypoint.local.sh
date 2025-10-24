#!/bin/sh

echo "" "Waiting for Postgres..."
while ! nc -z db 5432; do
  sleep 1
done
echo "" "Postgres is up!"

echo "" "Apply database migrations..."
python manage.py migrate
echo "" "Database migrations applied"

echo "" "Collecting static files..."
python manage.py collectstatic --noinput
echo "" "Static files collected"

echo "" "Starting server... local"
python manage.py runserver 0.0.0.0:8080
echo "" "Server started"
