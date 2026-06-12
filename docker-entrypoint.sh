#!/bin/bash
set -e

echo "Starting application setup..."

# Initialize the database and run migrations
flask db upgrade || flask db init && flask db migrate -m "Initial migration" && flask db upgrade

# Run custom init-db CLI command just in case
flask init-db

echo "Setup complete. Starting Gunicorn..."
exec "$@"
