#!/bin/sh
export PYTHONPATH=/app

echo "Waiting for database..."
while ! python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
  sleep 1
done
echo "Database ready."

alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
