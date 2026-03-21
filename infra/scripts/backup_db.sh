#!/usr/bin/env bash
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Backing up Qdrant..."
docker compose -f infra/docker-compose.yml exec qdrant \
  tar czf - /qdrant/storage > "$BACKUP_DIR/qdrant.tar.gz"

echo "Backup saved to $BACKUP_DIR"
