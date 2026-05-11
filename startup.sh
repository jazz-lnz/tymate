#!/bin/bash
# Azure App Service startup script for Flet web app
# Placed at repo root as startup.sh

set -e

echo "=== Tymate Flet App Startup ==="

# Install dependencies
pip install -r requirements.txt

# Azure sets PORT env var; Flet needs it via --port
PORT=${PORT:-8080}

echo "Starting Flet web app on port $PORT..."

# FLET_APP_VIEW=web is critical — tells Flet not to try opening a desktop window
export FLET_APP_VIEW=web

flet run main.py --web --port $PORT --host 0.0.0.0
