# backend/routes/students.py
# ─────────────────────────────────────────────────────────────
# REST endpoints for managing students.
# ─────────────────────────────────────────────────────────────

from flask import Blueprint, jsonify, request
from backend.utils.db import query, execute

students_bp = Blueprint("students", __name__)


@students_bp.route("/students", methods=["GET"])
def get_students():
    """GET /students  →  list of all enrolled students."""
    rows = query("SELECT id, name, roll_no, image_path, created_at FROM students ORDER BY name")
    return jsonify({"success": True, "students": rows})


@students_bp.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    """GET /students/<id>  →  single student."""
    row = query("SELECT * FROM students WHERE id = %s", (student_id,), fetchone=True)
    if not row:
        return jsonify({"success": False, "message": "Student not found"}), 404
    return jsonify({"success": True, "student": row})


@students_bp.route("/students", methods=["POST"])
def add_student():
    """POST /students  — body: {name, roll_no, image_path?}"""
    body = request.get_json() or {}
    name    = body.get("name", "").strip()
    roll_no = body.get("roll_no", "").strip()
    img     = body.get("image_path", "").strip()

    if not name or not roll_no:
        return jsonify({"success": False, "message": "name and roll_no are required"}), 400

    existing = query("SELECT id FROM students WHERE roll_no = %s", (roll_no,), fetchone=True)
    if existing:
        return jsonify({"success": False, "message": "Roll number already exists"}), 409

    new_id = execute(
        "INSERT INTO students (name, roll_no, image_path) VALUES (%s, %s, %s)",
        (name, roll_no, img or None)
    )
    return jsonify({"success": True, "message": "Student added", "id": new_id}), 201


@students_bp.route("/students/<int:student_id>/attendance", methods=["GET"])
def get_student_attendance(student_id):
    """Individual student attendance history + stats."""
    student = query("SELECT * FROM students WHERE id = %s", (student_id,), fetchone=True)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    rows = query(
        "SELECT date, time, status FROM attendance WHERE student_id=%s ORDER BY date DESC, time DESC",
        (student_id,)
    )
    for r in rows:
        r["date"] = str(r["date"])
        r["time"] = str(r["time"])

    total_present = query(
        "SELECT COUNT(*) AS c FROM attendance WHERE student_id=%s AND status='Present'",
        (student_id,), fetchone=True
    )["c"]

    total_working = query(
        "SELECT COUNT(DISTINCT date) AS c FROM attendance", fetchone=True
    )["c"]

    percentage = round((total_present / total_working * 100), 1) if total_working > 0 else 0

    last_seen = rows[0]["date"] if rows else "Never"

    monthly = query(
        """SELECT DATE_FORMAT(date,'%%Y-%%m') AS month, COUNT(*) AS present_days
           FROM attendance WHERE student_id=%s AND status='Present'
           GROUP BY month ORDER BY month DESC""",
        (student_id,)
    )

    return jsonify({
        "success": True,
        "student": {"id": student["id"], "name": student["name"], "roll_no": student["roll_no"]},
        "stats": {
            "total_present":      total_present,
            "total_working_days": total_working,
            "percentage":         percentage,
            "last_seen":          last_seen,
        },
        "monthly":    monthly,
        "attendance": rows,
    })
