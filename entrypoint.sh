#!/bin/sh
set -e

# wait for db if host is provided
if [ -n "$DB_HOST" ]; then
  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  until nc -z $DB_HOST $DB_PORT; do
    echo "Waiting for DB..."
    sleep 1
  done
fi

echo "Apply database migrations"
python manage.py migrate --noinput

echo "Collect static files"
python manage.py collectstatic --noinput

exec "$@"
