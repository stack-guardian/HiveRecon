#!/bin/bash
# Install systemd user service for HiveRecon auto-start on login
# Run: ./install-systemd-service.sh

SERVICE_FILE="$HOME/.config/systemd/user/hiverecon-server.service"
SERVICE_TEMPLATE="deploy/hiverecon-server.service"

mkdir -p "$HOME/.config/systemd/user"

cp "$SERVICE_TEMPLATE" "$SERVICE_FILE"
systemctl --user daemon-reload
systemctl --user enable hiverecon-server.service

echo "HiveRecon systemd service installed and enabled."
echo "It will auto-start on login and restart on failure."
