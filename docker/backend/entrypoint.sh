#!/bin/bash

echo "=== Zorix Backend Starting ==="

echo "Waiting for database..."
sleep 3

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000