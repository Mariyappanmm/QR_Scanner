#!/bin/bash
echo "Installing project dependencies..."
python3 -m pip install --break-system-packages --no-warn-script-location -r requirements.txt || python3 -m pip install -r requirements.txt

echo "Clearing Python bytecode caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Build process completed!"
