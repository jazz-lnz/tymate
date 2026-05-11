#!/bin/bash
# Azure App Service startup script for Tymate Sync Server
# Set this as your startup command in Azure:
#   bash startup.sh

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
