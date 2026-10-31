#!/usr/bin/env bash
# ==============================================================================
# FREY AI - Edge Service Shutdown Script
# Arduino UNO Q (Qualcomm QRB2210 Debian 13)
# ==============================================================================

PID_FILE="/tmp/frey.pid"
LOCK_FILE="/tmp/frey_camera.lock"

if [ ! -f "$PID_FILE" ]; then
    echo "[INFO] No active FREY AI service PID file found ($PID_FILE)."
    # Clean up lock just in case
    rm -f "$LOCK_FILE"
    exit 0
fi

PID=$(cat "$PID_FILE")
echo "[INFO] Stopping FREY AI service (PID $PID)..."

if ps -p "$PID" > /dev/null 2>&1; then
    kill -15 "$PID" 2>/dev/null || true

    # Wait up to 5 seconds for graceful shutdown
    COUNT=0
    while ps -p "$PID" > /dev/null 2>&1 && [ "$COUNT" -lt 5 ]; do
        sleep 1
        COUNT=$((COUNT + 1))
    done

    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[WARN] Process did not terminate within 5 seconds. Sending SIGKILL..."
        kill -9 "$PID" 2>/dev/null || true
    fi
    echo "[SUCCESS] FREY AI service stopped."
else
    echo "[INFO] Process $PID is not running."
fi

# Clean lock files
rm -f "$PID_FILE"
rm -f "$LOCK_FILE"
echo "[INFO] Cleaned lock files."
