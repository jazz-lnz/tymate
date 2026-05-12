#!/bin/bash
# startup.sh — at repo root
set -e

echo "=== Tymate Flet App Startup ==="

pip install -r requirements.txt --quiet

PORT=${PORT:-8080}
export FLET_APP_VIEW=web

echo "Starting on port $PORT..."

# Use python directly — avoids flet_desktop import that crashes on Linux server
python main.py