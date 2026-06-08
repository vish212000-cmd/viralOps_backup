#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Celery Worker..."
celery -A viralops worker -l info --pool=solo &

echo "Starting Celery Beat..."
celery -A viralops beat -l info &

echo "Starting Gunicorn Web Server..."
gunicorn viralops.wsgi:application --bind 0.0.0.0:$PORT
