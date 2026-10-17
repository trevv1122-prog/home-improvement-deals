#!/usr/bin/env bash
# Setup Daily Morning Deal Scan Cron Job (Default: 6:00 AM)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXEC="$(which python3)"
CRON_TIME="0 6 * * *" # At 06:00 every morning

echo "Configuring daily morning scan cron job at 06:00 AM..."
CRON_CMD="$CRON_TIME cd $SCRIPT_DIR && $PYTHON_EXEC scheduler.py --run-now >> $SCRIPT_DIR/morning_scan.log 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -F "scheduler.py") && {
    echo "Morning deal scanner cron job already installed."
    exit 0
}

# Append to crontab
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
echo "Successfully added to crontab:"
echo "  $CRON_CMD"
echo "Logs will be written to: $SCRIPT_DIR/morning_scan.log"
