# backend/routes/admin.py
# ─────────────────────────────────────────────────────────────
# Admin-only utilities:
#   POST /api/admin/retrain  — re-runs train_faces.py in-process
#   GET  /api/admin/stats    — DB row counts for dashboard
# ─────────────────────────────────────────────────────────────

import subprocess
import sys
import os
from flask import Blueprint, jsonify
from backend.utils.db import query

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/retrain", methods=["POST"])
def retrain():
    """Trigger face re-training from the browser (admin action)."""
    train_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "backend", "utils", "train_faces.py"
    )
    try:
        result = subprocess.run(
            [sys.executable, train_script],
            capture_output=True, text=True, timeout=120
        )
        success = result.returncode == 0
        return jsonify({
            "success": success,
            "output":  result.stdout[-2000:] if result.stdout else "",
            "errors":  result.stderr[-500:]  if result.stderr and not success else ""
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "message": "Training timed out (>120s)"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/admin/stats", methods=["GET"])
def stats():
    students   = query("SELECT COUNT(*) AS c FROM students",   fetchone=True)["c"]
    attendance = query("SELECT COUNT(*) AS c FROM attendance", fetchone=True)["c"]
    today_row  = query(
        "SELECT COUNT(*) AS c FROM attendance WHERE date = CURDATE()",
        fetchone=True
    )["c"]
    return jsonify({
        "total_students":        students,
        "total_attendance_rows": attendance,
        "present_today":         today_row
    })
