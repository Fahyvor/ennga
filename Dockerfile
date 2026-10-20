# Multi-stage build for optimal image size and speed
FROM python:3.13-slim-bookworm AS builder

# Set work directory
WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies for compiling Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        default-libmysqlclient-dev \
        pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Install python dependencies and create wheels
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

# Final runtime image
FROM python:3.13-slim-bookworm

# Create directory for the app user
RUN mkdir -p /home/app

# Create the app user and group
RUN addgroup --system app && adduser --system --group app

# Create appropriate application directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/ennga
ENV GUNICORN_CMD_ARGS="--no-control-socket"
RUN mkdir -p $APP_HOME/static $APP_HOME/media $APP_HOME/static_in_env /home/app/.ssh /home/app/.gunicorn && \
    chmod 700 /home/app/.ssh /home/app/.gunicorn
WORKDIR $APP_HOME

# Install runtime system dependencies (SSH tunneling, database clients, font & image libraries, network utilities)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd \
        openssh-client \
        autossh \
        sshpass \
        libpq5 \
        default-mysql-client \
        fontconfig \
        libfreetype6 && \
    rm -rf /var/lib/apt/lists/*

# Install pre-built wheels
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy entrypoint.sh and normalize line endings
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' $APP_HOME/entrypoint.sh && \
    chmod +x $APP_HOME/entrypoint.sh

# Copy project source files
COPY . $APP_HOME

# Pre-collect static assets so image is self-contained and starts immediately
RUN python manage.py collectstatic --noinput || true

# Fix permissions for the non-root app user
RUN chown -R app:app /home/app

# Switch to non-root user
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/health/ || exit 1

ENTRYPOINT ["/home/app/ennga/entrypoint.sh"]

CMD ["sh", "-c", "exec gunicorn ennga.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120 --no-control-socket"]