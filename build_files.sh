#!/usr/bin/env bash
set -e

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --settings=carhaki.settings.vercel

echo "==> Running database migrations..."
python manage.py migrate --settings=carhaki.settings.vercel

echo "==> Build complete."
