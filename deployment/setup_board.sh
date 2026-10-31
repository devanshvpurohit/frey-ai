#!/usr/bin/env bash
# ==============================================================================
# FREY AI - Arduino UNO Q Board Setup Script
# Target: Qualcomm QRB2210 quad-core ARM64 / Debian GNU/Linux 13 (Trixie)
#
# Adheres strictly to PEP 668 (externally-managed-environment) on Debian 13.
# Prioritizes Debian apt-get packages for OpenCV, NumPy, and Flask.
# ==============================================================================

set -e

echo "=========================================================="
echo "         FREY AI - ARDUINO UNO Q SETUP WIZARD            "
echo "=========================================================="
echo "Target OS: Debian GNU/Linux 13 (aarch64)"
echo "Processor: Qualcomm QRB2210 (4GB RAM)"
echo "=========================================================="

# 1. Verify Architecture
ARCH=$(uname -m)
echo "[INFO] Detected system architecture: $ARCH"

# 2. Update Debian package lists
echo "\n[STEP 1/5] Updating Debian 13 apt repositories..."
if [ "$(id -u)" -eq 0 ]; then
    apt-get update -y
    apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-dev \
        python3-pip \
        python3-numpy \
        python3-opencv \
        python3-flask \
        sqlite3 \
        v4l-utils \
        libgl1 \
        libglib2.0-0 \
        curl
else
    sudo apt-get update -y
    sudo apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-dev \
        python3-pip \
        python3-numpy \
        python3-opencv \
        python3-flask \
        sqlite3 \
        v4l-utils \
        libgl1 \
        libglib2.0-0 \
        curl
fi

# 3. Setup PEP 668 Compliant Isolated Python Environment
# Using --system-site-packages allows using high-performance pre-compiled apt
# packages for OpenCV and NumPy while keeping pip installations isolated.
echo "\n[STEP 2/5] Creating PEP 668-compliant virtual environment with system site-packages..."
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$DEPLOY_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv --system-site-packages "$VENV_DIR"
    echo "[INFO] Created virtual environment at $VENV_DIR"
else
    echo "[INFO] Virtual environment already exists at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# 4. Install Edge Inference Engine (ONNX Runtime if available for aarch64)
echo "\n[STEP 3/5] Verifying ONNX runtime backend..."
python3 -c "import cv2; print('[CHECK] OpenCV DNN backend available:', hasattr(cv2.dnn, 'readNetFromONNX'))"

echo "[INFO] Probing onnxruntime availability..."
if python3 -c "import onnxruntime" 2>/dev/null; then
    echo "[CHECK] onnxruntime is already installed and functional."
else
    echo "[INFO] Attempting to install onnxruntime inside isolated venv..."
    pip install --no-cache-dir onnxruntime || {
        echo "[WARN] onnxruntime wheel not available directly via pip for this architecture."
        echo "[INFO] FREY AI will seamlessly use OpenCV DNN (cv2.dnn) for ONNX inference on Qualcomm ARM."
    }
fi

# 5. Check Video Devices & Permissions
echo "\n[STEP 4/5] Probing USB Camera devices..."
if [ -c /dev/video0 ]; then
    echo "[SUCCESS] Found /dev/video0"
    v4l2-ctl --list-devices 2>/dev/null || true
else
    echo "[NOTICE] No /dev/video0 device detected yet. When you plug in a USB webcam, it will be auto-detected."
    echo "[INFO] Ensure your user has access to the video group:"
    echo "       sudo usermod -aG video $USER"
fi

# 6. Verify Model Assets
echo "\n[STEP 5/5] Verifying ONNX model and taxonomy..."
if [ -f "$DEPLOY_DIR/models/frey_yolo11n_416.onnx" ]; then
    echo "[SUCCESS] Found ONNX model: $DEPLOY_DIR/models/frey_yolo11n_416.onnx"
else
    echo "[WARN] ONNX model not found in models/."
    echo "       Please copy your exported frey_yolo11n_416.onnx into deployment/models/ before starting."
fi

# Make start/stop scripts executable
chmod +x "$DEPLOY_DIR/start_frey.sh" "$DEPLOY_DIR/stop_frey.sh"

echo "\n=========================================================="
echo "             BOARD SETUP COMPLETE                         "
echo "=========================================================="
echo "To start FREY AI, run:"
echo "  cd $DEPLOY_DIR && ./start_frey.sh"
echo "To stop FREY AI, run:"
echo "  cd $DEPLOY_DIR && ./stop_frey.sh"
echo "=========================================================="
