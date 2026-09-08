#!/bin/bash
echo "Installing project dependencies..."
python3 -m pip install --break-system-packages --no-warn-script-location -r requirements.txt || python3 -m pip install -r requirements.txt

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Running Database Migrations..."
python3 manage.py migrate --noinput

echo "Build process completed!"
