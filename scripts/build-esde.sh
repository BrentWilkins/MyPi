#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$ROOT_DIR/dist"

echo "Building ES-DE for linux/arm64..."
docker buildx build \
    --platform linux/arm64 \
--file "$ROOT_DIR/docker/Dockerfile.esde" \
    --target export \
    --output "type=local,dest=$DIST_DIR" \
    "$ROOT_DIR"

echo ""
echo "Binary written to $DIST_DIR/es-de"
ls -lh "$DIST_DIR/es-de"
