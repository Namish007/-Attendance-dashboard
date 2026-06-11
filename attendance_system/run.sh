


set -e
cd "$(dirname "$0")"

echo ""
echo "====================================================="
echo "  AI-Based Smart Attendance System — NIET"
echo "====================================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Install Python 3.10+ first."
    exit 1
fi

PYTHON=python3


if ! $PYTHON -c "import flask" &>/dev/null; then
    echo "[INFO] Installing dependencies..."
    $PYTHON -m pip install -r requirements.txt
fi


if [ ! -f "models/encodings.pkl" ]; then
    echo "[WARN] Face encodings not found."
    read -p "       Run training now? (y/n) > " choice
    if [ "$choice" = "y" ]; then
        echo "[INFO] Training face model..."
        $PYTHON backend/utils/train_faces.py
    fi
fi

echo ""
echo "[INFO] Starting Flask server..."
echo "[INFO] Open browser at: http://localhost:5000"
echo "[INFO] Press Ctrl+C to stop."
echo ""

$PYTHON backend/app.py
