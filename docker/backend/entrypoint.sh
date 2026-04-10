#!/bin/bash
set -e

echo "=== Zorix Backend Starting ==="

echo "Waiting for database..."
sleep 3

echo "Starting FastAPI server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000