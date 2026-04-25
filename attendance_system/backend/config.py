# backend/config.py
# ─────────────────────────────────────────────────────────────
# Central configuration — edit here, changes apply everywhere.
# ─────────────────────────────────────────────────────────────
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── MySQL ─────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_USER     = "root"
DB_PASSWORD = ""          # blank by default in XAMPP
DB_NAME     = "attendance_system"

# ── Paths ─────────────────────────────────────────────────────
DATASET_DIR    = os.path.join(BASE_DIR, "dataset")
MODELS_DIR     = os.path.join(BASE_DIR, "models")
ENCODING_FILE  = os.path.join(MODELS_DIR, "encodings.pkl")

# ── Recognition ───────────────────────────────────────────────
FACE_TOLERANCE = 0.50     # 0.4 = strict, 0.6 = lenient
FRAME_SCALE    = 0.5      # resize factor before recognition (speed vs accuracy)

# ── Flask ─────────────────────────────────────────────────────
FLASK_HOST  = "0.0.0.0"
FLASK_PORT  = 5000
FLASK_DEBUG = True

# ── Attendance ────────────────────────────────────────────────
# How many seconds must pass before the same student can be
# marked again within one session (prevents rapid re-marking).
MIN_MARK_INTERVAL_SECONDS = 5
