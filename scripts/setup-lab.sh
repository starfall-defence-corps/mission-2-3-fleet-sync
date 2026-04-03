#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$ROOT_DIR/.docker"
SSH_DIR="$DOCKER_DIR/ssh-keys"

echo ""
echo "=============================================="
echo "  STARFALL DEFENCE CORPS ACADEMY"
echo "  Mission 2.3: Fleet-Wide Operations"
echo "  Initialising Fleet + Load Balancer..."
echo "=============================================="
echo ""

if ! python3 -m venv --help &>/dev/null; then
    echo "  ERROR: python3-venv is not installed."
    echo "  On Debian/Ubuntu: sudo apt install python3-venv"
    echo "  On Fedora/RHEL:   sudo dnf install python3-virtualenv"
    exit 1
fi

if [ ! -d "$ROOT_DIR/venv" ]; then
    echo "  Setting up Python environment..."
    python3 -m venv "$ROOT_DIR/venv"
    "$ROOT_DIR/venv/bin/pip" install -q -r "$ROOT_DIR/requirements.txt"
    "$ROOT_DIR/venv/bin/ansible-galaxy" collection install community.general ansible.posix > /dev/null
    echo "  Python environment ready."
    echo ""
fi

if [ ! -f "$SSH_DIR/cadet_key" ]; then
    echo "  Generating SSH credentials..."
    mkdir -p "$SSH_DIR"
    ssh-keygen -t ed25519 -f "$SSH_DIR/cadet_key" -N "" -C "cadet@starfall-academy" -q
    cp "$SSH_DIR/cadet_key.pub" "$SSH_DIR/authorized_keys"
    chmod 600 "$SSH_DIR/cadet_key"
    chmod 644 "$SSH_DIR/authorized_keys"
    echo "  SSH credentials generated."
    echo ""
fi

mkdir -p "$ROOT_DIR/workspace/.ssh"
cp "$SSH_DIR/cadet_key" "$ROOT_DIR/workspace/.ssh/cadet_key"
chmod 600 "$ROOT_DIR/workspace/.ssh/cadet_key"

cat > "$ROOT_DIR/workspace/.ssh/testinfra_ssh_config" << 'SSHEOF'
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
SSHEOF

echo "  Building fleet and infrastructure..."
docker compose -f "$DOCKER_DIR/docker-compose.yml" up -d --build 2>&1 | while read -r line; do
    echo "    $line"
done

echo ""
echo "  Waiting for SSH to become available..."
for node in sdc-app-1:2261 sdc-app-2:2262 sdc-app-3:2263 sdc-app-4:2264 sdc-lb:2265 sdc-monitor:2266; do
    name="${node%%:*}"
    port="${node##*:}"
    for i in $(seq 1 30); do
        if ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=1 \
            -i "$SSH_DIR/cadet_key" cadet@localhost -p "$port" exit 2>/dev/null; then
            echo "    $name (port $port): ONLINE"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "    $name (port $port): TIMEOUT — check 'docker compose logs $name'"
        fi
        sleep 1
    done
done

echo ""
echo "  Verifying load balancer..."
sleep 2
LB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
if [ "$LB_STATUS" = "200" ]; then
    echo "    HAProxy (port 8080): SERVING"
    echo "    Stats dashboard: http://localhost:8404/stats"
else
    echo "    HAProxy (port 8080): NOT READY (status $LB_STATUS)"
    echo "    Check: docker compose logs sdc-lb"
fi

echo ""
echo "=============================================="
echo "  Fleet:         4 app servers ONLINE"
echo "  Load Balancer: 1 HAProxy ONLINE"
echo "  Monitor:       1 node ONLINE"
echo ""
echo "  The fleet needs a rolling update."
echo "  Zero downtime. No excuses."
echo ""
echo "  Your workspace: workspace/"
echo "  Start here:     docs/BRIEFING.md"
echo "  Verify work:    make test"
echo ""
echo "  Remember to activate your environment:"
echo "    source venv/bin/activate"
echo "=============================================="
echo ""
