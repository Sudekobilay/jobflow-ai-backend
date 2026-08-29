#!/bin/sh
set -e

if [ "$(id -u)" = "0" ]; then
  mkdir -p /app/staticfiles /app/media
  chown -R webuser:webuser /app/staticfiles /app/media
  exec gosu webuser "$0" "$@"
fi

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

if [ "$APP_ENV" = "production" ]; then
  echo "Running production deployment checks"
  python manage.py check --deploy --settings "$DJANGO_SETTINGS_MODULE"
fi

echo "Collect static files"
python manage.py collectstatic --noinput

exec "$@"
