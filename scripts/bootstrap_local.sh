#!/usr/bin/env bash
# Bootstrap script to build and start local Docker containers for OER_Phoenix
set -e

echo "Building OER_Phoenix containers…"
docker compose build

echo "Starting containers…"
docker compose up -d

echo "Tailing web logs (Ctrl+C to stop)…"
docker compose logs -f web
