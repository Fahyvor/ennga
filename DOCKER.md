# Docker Deployment Guide for ENNGA Platform

This guide provides instructions for deploying and running the **ENNGA** server using Docker and Docker Compose.

---

## Architecture Overview

The containerized stack consists of:
- **`ennga` (Web)**: Django application running via Gunicorn (Python 3.13-slim) with non-root security.
- **`celery` (Worker & Beat)**: Asynchronous task processor & recurring scheduler.
- **`db` (PostgreSQL)**: PostgreSQL 15 database service with healthchecks and persistent volumes.
- **`redis` (Cache & Broker)**: In-memory cache and Celery task broker.
- **`nginx` (Gateway)**: High-performance reverse proxy serving static and media assets.
- **`elasticsearch` (Search)**: Search indexing service.

---

## Quick Start (Development / Local Stack)

### 1. Copy Environment Configuration
```bash
cp .env.example .env
```
*(The default settings in `docker-compose.yml` work out-of-the-box with the containerized Postgres and Redis services).*

### 2. Build and Start Services
```bash
docker compose up --build -d
```

### 3. Check Service Status & Logs
```bash
docker compose ps
docker compose logs -f ennga
```

The application will be accessible at:
- Web App (Direct): `http://localhost:8000/`
- Web App (via Nginx Reverse Proxy): `http://localhost:80/` or `http://localhost:8080/`

---

## Common Management Tasks

### Create Superuser
```bash
docker compose exec ennga python manage.py createsuperuser
```

### Run Migrations Manually
*(Migrations run automatically on container startup via `entrypoint.sh`)*
```bash
docker compose exec ennga python manage.py migrate
```

### Collect Static Files Manually
```bash
docker compose exec ennga python manage.py collectstatic --noinput
```

### Open Django Shell
```bash
docker compose exec ennga python manage.py shell
```

### Access PostgreSQL CLI
```bash
docker compose exec db psql -U ennga_user -d ennga_db
```

### Stop the Containers
```bash
docker compose down
```
To stop and remove persistent volumes (fresh database):
```bash
docker compose down -v
```

---

## Production Deployment

For production deployments on a server/VPS:

1. Configure your `.env` file with `DEBUG=False`, your domain names in `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, and production database credentials.
2. Launch using the production compose configuration:
   ```bash
   docker compose -f docker-compose.prod.yml up --build -d
   ```
3. Nginx will route port `80` and `443` directly to the Gunicorn workers.

---

## Cloud Platform Deployments (Render, AWS ECS, DigitalOcean App Platform, Fly.io)

The `Dockerfile` is built to be cloud-native and deployable as a standalone container:
- **Automatic Port Binding**: Uses `${PORT:-8000}`, dynamically adapting to Render or AWS ECS port assignment.
- **Embedded Static Serving (WhiteNoise)**: With `whitenoise` integrated, CSS, JS, fonts, and images are served directly and efficiently by the container with compression and cache headers without needing a separate Nginx container.
- **Healthcheck Endpoint**: Pre-configured `HEALTHCHECK` hitting `http://127.0.0.1:${PORT:-8000}/health/`. This same endpoint can be configured on Render Health Checks and UptimeRobot to keep the service warm.
- **Security & Privileges**: Runs as an unprivileged user (`app`) with appropriate file and socket permissions.
- **Fast Startup**: Pre-compiles Python wheels in a multi-stage build and pre-collects static assets during image creation.
- **Remote DB & SSH Tunneling**: If using a remote MySQL/Postgres database (e.g., Namecheap cPanel), set `USE_SSH_TUNNEL=true`, `SSH_HOST`, `SSH_PORT=21098`, `SSH_USER`, and `SSH_PRIVATE_KEY` in environment variables; `entrypoint.sh` will automatically establish the secure tunnel before booting the web server.

