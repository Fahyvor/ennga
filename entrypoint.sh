#!/bin/sh

set -e

# ==========================================
# SSH TUNNEL CONFIGURATION (for remote DBs e.g. Namecheap)
# ==========================================
USE_SSH_TUNNEL="${USE_SSH_TUNNEL:-false}"
SSH_TUNNEL="${SSH_TUNNEL:-false}"

if [ "$USE_SSH_TUNNEL" = "true" ] || [ "$SSH_TUNNEL" = "true" ] || [ -n "$SSH_HOST" ]; then
    echo "=========================================="
    echo "Configuring SSH Tunnel for Database..."
    echo "=========================================="

    SSH_HOST="${SSH_HOST:-premium214.web-hosting.com}"
    SSH_PORT="${SSH_PORT:-21098}"
    SSH_USER="${SSH_USER:-kuledwzl}"
    SSH_LOCAL_PORT="${SSH_LOCAL_PORT:-3306}"
    SSH_REMOTE_HOST="${SSH_REMOTE_HOST:-127.0.0.1}"
    SSH_REMOTE_PORT="${SSH_REMOTE_PORT:-3306}"

    SSH_DIR="/home/app/.ssh"
    mkdir -p "$SSH_DIR"
    chmod 700 "$SSH_DIR"

    SSH_KEY_FILE="$SSH_DIR/id_rsa"
    SSH_AUTH_ARGS=""

    if [ -n "$SSH_PRIVATE_KEY" ]; then
        echo "Installing SSH Private Key..."
        # Decode base64 if key doesn't start with -----BEGIN, or replace literal \n
        if echo "$SSH_PRIVATE_KEY" | grep -q -- "BEGIN"; then
            printf "%b\n" "$SSH_PRIVATE_KEY" > "$SSH_KEY_FILE"
        else
            echo "$SSH_PRIVATE_KEY" | base64 -d > "$SSH_KEY_FILE" 2>/dev/null || printf "%b\n" "$SSH_PRIVATE_KEY" > "$SSH_KEY_FILE"
        fi
        chmod 600 "$SSH_KEY_FILE"
        SSH_AUTH_ARGS="-i $SSH_KEY_FILE"
        echo "SSH Private Key configured."
    fi

    SSH_COMMON_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes"

    echo "Establishing SSH tunnel: 127.0.0.1:${SSH_LOCAL_PORT} -> ${SSH_HOST}:${SSH_PORT} -> ${SSH_REMOTE_HOST}:${SSH_REMOTE_PORT} (user: ${SSH_USER})"

    if [ -n "$SSH_PASSWORD" ] && [ -z "$SSH_PRIVATE_KEY" ]; then
        echo "Authenticating SSH using password..."
        export SSHPASS="$SSH_PASSWORD"
        sshpass -e ssh -f -N \
            $SSH_COMMON_OPTS \
            -L 0.0.0.0:${SSH_LOCAL_PORT}:${SSH_REMOTE_HOST}:${SSH_REMOTE_PORT} \
            -p ${SSH_PORT} \
            ${SSH_USER}@${SSH_HOST}
    else
        # Prefer autossh for auto-reconnection on network drops
        if command -v autossh >/dev/null 2>&1; then
            AUTOSSH_GATETIME=0 autossh -M 0 -f -N \
                $SSH_COMMON_OPTS \
                -L 0.0.0.0:${SSH_LOCAL_PORT}:${SSH_REMOTE_HOST}:${SSH_REMOTE_PORT} \
                -p ${SSH_PORT} \
                $SSH_AUTH_ARGS \
                ${SSH_USER}@${SSH_HOST}
        else
            ssh -f -N \
                $SSH_COMMON_OPTS \
                -L 0.0.0.0:${SSH_LOCAL_PORT}:${SSH_REMOTE_HOST}:${SSH_REMOTE_PORT} \
                -p ${SSH_PORT} \
                $SSH_AUTH_ARGS \
                ${SSH_USER}@${SSH_HOST}
        fi
    fi

    echo "Verifying local tunnel on port ${SSH_LOCAL_PORT}..."
    TUNNEL_READY=0
    for i in $(seq 1 25); do
        if nc -z 127.0.0.1 "${SSH_LOCAL_PORT}" 2>/dev/null; then
            echo "SSH Tunnel is ACTIVE on 127.0.0.1:${SSH_LOCAL_PORT}!"
            TUNNEL_READY=1
            break
        fi
        sleep 1
    done

    if [ $TUNNEL_READY -eq 0 ]; then
        echo "WARNING: Could not verify SSH tunnel on 127.0.0.1:${SSH_LOCAL_PORT} within 25 seconds."
        echo "Check if your SSH credentials (SSH_PRIVATE_KEY or SSH_PASSWORD), SSH_HOST, and SSH_PORT are correct."
    fi
fi

# ==========================================
# DATABASE MIGRATIONS
# ==========================================
echo "Applying database migrations..."
if ! python manage.py migrate --noinput; then
    echo "=========================================="
    echo "WARNING / ERROR: Database migration failed."
    echo "If using a remote database on Namecheap, make sure:"
    echo "1. USE_SSH_TUNNEL=true is set in your environment."
    echo "2. SSH_PRIVATE_KEY (or SSH_PASSWORD) is provided in Render."
    echo "3. SSH_PORT is set to 21098 (Namecheap SSH port)."
    echo "=========================================="
    # If migrations fail, we exit so Render doesn't start an unhealthy service
    exit 1
fi

# ==========================================
# STATIC ASSETS
# ==========================================
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application process..."
exec "$@"