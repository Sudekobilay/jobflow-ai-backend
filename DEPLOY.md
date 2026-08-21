# Deployment and rollback guide

## 1. Production database migration plan

### Backup

```bash
mysqldump -u root -p$MYSQL_ROOT_PASSWORD jobflow_db > jobflow_db_backup.sql
```

If the database is running in Docker:

```bash
docker compose exec db mysqldump -u root -p$MYSQL_ROOT_PASSWORD jobflow_db > jobflow_db_backup.sql
```

### DB user privilege check

Verify the application database user can create/alter tables for the target database.

```sql
SHOW GRANTS FOR 'jobflow_user'@'%';
CREATE TABLE IF NOT EXISTS jobflow_db.__priv_test (id INT PRIMARY KEY);
DROP TABLE IF EXISTS jobflow_db.__priv_test;
```

The application user must have at least:

- SELECT
- INSERT
- UPDATE
- DELETE
- CREATE
- ALTER
- INDEX

### Run migrations

```bash
docker compose exec web python manage.py migrate --noinput
```

### Smoke tests

#### Auth

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"qa@example.com","password":"StrongPass123!","first_name":"QA","last_name":"Tester"}'

curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"qa@example.com","password":"StrongPass123!"}'
```

#### Profile

```bash
curl -X GET http://localhost:8000/api/profiles/me/ \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### Jobs

```bash
curl -X GET http://localhost:8000/api/jobs/ \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### AI endpoints

```bash
curl -X POST http://localhost:8000/api/ai/summary/ \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"text":"Senior Python Django engineer with 5 years in fintech and AI automation."}'

curl -X POST http://localhost:8000/api/ai/match/ \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"cv_text":"Python, Django, REST, Postgres, team leadership","job_description":"Python backend engineer with Django, API integration, and data processing skills."}'
```

#### Applications

```bash
curl -X GET http://localhost:8000/api/applications/cv/ \
  -H "Authorization: Bearer <JWT_TOKEN>"

curl -X GET http://localhost:8000/api/applications/applications/ \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

## 2. Static and media handling

Production should run Django with `collectstatic` and serve static/media via Nginx.

```bash
docker compose exec web python manage.py collectstatic --noinput
```

Verify these values in production settings:

- `DEBUG = False`
- `STATIC_ROOT` points to a writable static directory
- `MEDIA_ROOT` points to a writable media directory
- Nginx proxies `/static/` and `/media/` from the mounted Docker volumes

## 3. Logging and error tracking

Set the following environment variables in the production environment:

```bash
export SENTRY_DSN="https://<key>@o<org>.ingest.sentry.io/<project>"
export SENTRY_TRACE_SAMPLE_RATE="0.1"
```

When `SENTRY_DSN` is configured, the app initializes Sentry automatically via the Django integration.

## 4. Release and deployment

### Build image

```bash
docker build -t yourdockerhubusername/jobflow-ai-backend:latest .
```

### Push image

```bash
docker push yourdockerhubusername/jobflow-ai-backend:latest
```

### Run via docker compose

```bash
docker compose up -d --build
```

### Rollback

1. Stop the current stack:

```bash
docker compose down
```

2. Revert to the previous image tag:

```bash
docker compose up -d --force-recreate
```

3. Restore the database from the latest backup if needed:

```bash
mysql -u root -p$MYSQL_ROOT_PASSWORD jobflow_db < jobflow_db_backup.sql
```

## 5. Security hardening checklist

- `DEBUG=False` in production settings
- Strict `ALLOWED_HOSTS`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_*` enabled
- `CORS_ALLOW_ALL_ORIGINS=False` in production
- Restrict origins via `CORS_ALLOWED_ORIGINS`
- Use HTTPS and reverse proxy termination through Nginx
- Run behind a proper WAF/reverse proxy in production

## 6. Postman smoke checks

Import the collection file `postman_collection.json` and run:

1. Register user
2. Login and capture JWT
3. Fetch profile
4. List jobs
5. Create a job
6. Create a CV
7. Create job application
8. Call AI summary and AI match endpoints

## 7. Roll-forward notes

After the migration and smoke tests succeed, tag the release and keep the last known-good backup and image tag for quick rollback.
