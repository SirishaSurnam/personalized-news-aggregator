#!/bin/bash

# Exit on any error
set -e

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
        sleep 1
    done
    echo "PostgreSQL is ready!"
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis to be ready..."
    while ! nc -z $REDIS_HOST $REDIS_PORT; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Wait for services
wait_for_postgres
wait_for_redis

# Handle different commands
case "$1" in
    "web")
        echo "Starting Django web server..."
        python manage.py migrate --noinput
        python manage.py collectstatic --noinput
        exec python manage.py runserver 0.0.0.0:8000
        ;;
    "celery")
        if [ "$2" = "worker" ]; then
            echo "Starting Celery worker..."
            exec celery -A news_aggregator worker --loglevel=info
        elif [ "$2" = "beat" ]; then
            echo "Starting Celery beat..."
            exec celery -A news_aggregator beat --loglevel=info
        else
            echo "Unknown celery command: $2"
            exit 1
        fi
        ;;
    *)
        echo "Executing command: $@"
        exec "$@"
        ;;
esac