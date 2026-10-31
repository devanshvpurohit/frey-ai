#!/usr/bin/env bash
# ==============================================================================
# FREY AI - Edge Service Startup Script
# Arduino UNO Q (Qualcomm QRB2210 Debian 13)
# ==============================================================================

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="/tmp/frey.pid"
LOG_FILE="$DEPLOY_DIR/frey.log"

cd "$DEPLOY_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[ERROR] FREY AI is already running (PID $PID)."
        echo "Run ./stop_frey.sh first if you wish to restart."
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# Clean stale camera locks
rm -f /tmp/frey_camera.lock

# Activate venv if present
if [ -d "$DEPLOY_DIR/.venv" ]; then
    source "$DEPLOY_DIR/.venv/bin/activate"
fi

# Set PYTHONPATH to include deployment folder
export PYTHONPATH="$DEPLOY_DIR:$PYTHONPATH"

# Verify model file
if [ ! -f "$DEPLOY_DIR/models/frey_yolo11n_416.onnx" ]; then
    echo "[ERROR] Model file missing: $DEPLOY_DIR/models/frey_yolo11n_416.onnx"
    echo "Please ensure the ONNX model is copied to deployment/models/ before starting."
    exit 1
fi

PORT="${1:-5000}"
HOST="0.0.0.0"

echo "=========================================================="
echo "           STARTING FREY AI EDGE SERVICE                  "
echo "=========================================================="
echo "Deployment Root : $DEPLOY_DIR"
echo "Log File        : $LOG_FILE"
echo "Listening On    : http://$HOST:$PORT"

# Detect IP addresses on board
IP_LIST=$(hostname -I 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' || echo "localhost")
echo "Local Dashboard Access URLs:"
for IP in $IP_LIST; do
    echo "  -> http://$IP:$PORT"
done
echo "=========================================================="

# Launch server in background
nohup python3 frey/server.py --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

# Wait 2 seconds and check if process is alive
sleep 2
if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    echo "[SUCCESS] FREY AI daemon started with PID $SERVER_PID."
    echo "View live logs with: tail -f $LOG_FILE"
else
    echo "[ERROR] FREY AI failed to start. Last log output:"
    cat "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
