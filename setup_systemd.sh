#!/usr/bin/env bash
# Create a systemd user timer for 6:00 AM daily morning scan
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXEC="$(which python3)"
SERVICE_DIR="$HOME/.config/systemd/user"

mkdir -p "$SERVICE_DIR"

cat << EOF > "$SERVICE_DIR/deal-scanner.service"
[Unit]
Description=Home Depot & Lowe's Morning Deal Scanner
After=network.target

[Service]
Type=oneshot
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON_EXEC $SCRIPT_DIR/scheduler.py --run-now
StandardOutput=append:$SCRIPT_DIR/morning_scan.log
StandardError=append:$SCRIPT_DIR/morning_scan.log
EOF

cat << EOF > "$SERVICE_DIR/deal-scanner.timer"
[Unit]
Description=Run deal-scanner daily at 6:00 AM

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload || true
systemctl --user enable --now deal-scanner.timer || true

echo "Systemd timer configured for daily 6:00 AM deal scans."
