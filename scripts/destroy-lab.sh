#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$ROOT_DIR/.docker"

echo ""
echo "=============================================="
echo "  Decommissioning fleet and infrastructure..."
echo "=============================================="
echo ""

if [ -f "$DOCKER_DIR/docker-compose.yml" ]; then
    docker compose -f "$DOCKER_DIR/docker-compose.yml" down -v 2>&1 | while read -r line; do
        echo "    $line"
    done
fi

rm -rf "$DOCKER_DIR/ssh-keys"
rm -rf "$ROOT_DIR/workspace/.ssh"
rm -rf "$ROOT_DIR/venv"

echo ""
echo "  Fleet and infrastructure decommissioned."
echo ""
