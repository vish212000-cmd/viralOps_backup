#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Gunicorn Web Server..."
gunicorn viralops.wsgi:application --bind 0.0.0.0:$PORT
