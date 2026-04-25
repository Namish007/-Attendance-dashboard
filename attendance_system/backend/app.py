# backend/app.py
# Run from project root:  python backend/app.py
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from backend.config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, DATASET_DIR, MODELS_DIR
from backend.routes.students   import students_bp
from backend.routes.attendance import attendance_bp
from backend.routes.export     import export_bp
from backend.routes.enroll     import enroll_bp
from backend.routes.admin      import admin_bp

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(MODELS_DIR,  exist_ok=True)

FRONTEND_DIR = os.path.join(ROOT, "frontend")
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

for bp in [students_bp, attendance_bp, export_bp, enroll_bp, admin_bp]:
    app.register_blueprint(bp, url_prefix="/api")

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "AI Attendance System running"})

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  AI-Based Smart Attendance System")
    print(f"  Server  →  http://localhost:{FLASK_PORT}")
    print(f"  Dataset →  {DATASET_DIR}")
    print(f"  Models  →  {MODELS_DIR}")
    print("="*55 + "\n")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
