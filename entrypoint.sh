#!/bin/bash

# Exit on any error
set -e

# Function to wait for database
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z db 5432; do
        sleep 1
    done
    echo "Database is ready!"
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z redis 6379; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Wait for services if running web service
if [ "$1" = "web" ] || [ "$1" = "gunicorn" ]; then
    wait_for_db
    wait_for_redis
    
    echo "Running database migrations..."
    python manage.py migrate --noinput
    
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
    
    echo "Starting Gunicorn..."
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi

# Wait for services if running celery
if [ "$1" = "celery" ]; then
    wait_for_db
    wait_for_redis
    
    if [ "$2" = "worker" ]; then
        echo "Starting Celery Worker..."
        exec celery -A config worker -l info
    elif [ "$2" = "beat" ]; then
        echo "Starting Celery Beat..."
        exec celery -A config beat -l info --scheduler django_celery_beat.schedulers.DatabaseScheduler
    fi
fi

# Execute the original command
exec "$@"