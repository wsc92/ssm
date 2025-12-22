#!/bin/bash

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Install location
INSTALL_DIR="/opt/security-scanner"
LOG_DIR="/var/log/scanner"

echo "Installing security scanner to $INSTALL_DIR..."

# Copy files
mkdir -p "$INSTALL_DIR"
cp -r src config pyproject.toml "$INSTALL_DIR/"

# Create log directory
mkdir -p "$LOG_DIR"

# Install systemd units
cp config/scanner.service /etc/systemd/system/
cp config/scanner.timer /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start timer
systemctl enable scanner.timer
systemctl start scanner.timer

echo "Installation complete!"
echo ""
echo "Usage:"
echo "  Start timer:  systemctl start scanner.timer"
echo "  Stop timer:   systemctl stop scanner.timer"
echo "  View logs:    journalctl -u scanner.service"
echo "  View reports: cat /var/log/scanner/report.json"
