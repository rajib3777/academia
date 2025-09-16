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

echo "" "Starting server..."
gunicorn classmate.wsgi:application --bind 0.0.0.0:80 --workers 3 --log-level info --log-file -
# uvicorn classmate.asgi:application --host 0.0.0.0 --port 80 --workers 3 --log-level info --log-file - -reload &

echo "" "Server started"
