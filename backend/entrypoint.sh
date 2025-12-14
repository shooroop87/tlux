#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Starting gunicorn..."
exec "$@"