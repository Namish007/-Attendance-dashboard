# backend/routes/attendance.py
# ─────────────────────────────────────────────────────────────
# REST endpoints for attendance operations.
# ─────────────────────────────────────────────────────────────

import base64
import numpy as np
import cv2
from datetime import date, datetime
from flask import Blueprint, jsonify, request
from backend.utils.db import query, execute
from backend.utils.recognizer import identify_face_from_frame, annotate_frame

attendance_bp = Blueprint("attendance", __name__)


# ── helpers ────────────────────────────────────────────────────

def _student_by_roll(roll_no: str):
    return query(
        "SELECT id, name, roll_no FROM students WHERE roll_no = %s",
        (roll_no,), fetchone=True
    )


def _already_marked(student_id: int, today: str) -> bool:
    row = query(
        "SELECT id FROM attendance WHERE student_id=%s AND date=%s",
        (student_id, today), fetchone=True
    )
    return row is not None


def _decode_frame(b64_image: str) -> np.ndarray | None:
    """Decode a base64 JPEG/PNG data-URL into a BGR ndarray."""
    try:
        if "," in b64_image:
            b64_image = b64_image.split(",", 1)[1]
        raw  = base64.b64decode(b64_image)
        arr  = np.frombuffer(raw, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


# ── routes ────────────────────────────────────────────────────

@attendance_bp.route("/attendance", methods=["GET"])
def get_attendance():
    """
    GET /attendance?date=YYYY-MM-DD
    Returns all attendance records (optionally filtered by date).
    """
    filter_date = request.args.get("date", "")
    if filter_date:
        rows = query(
            """SELECT a.id, s.name, s.roll_no, a.date, a.time, a.status
               FROM attendance a
               JOIN students s ON s.id = a.student_id
               WHERE a.date = %s
               ORDER BY a.time DESC""",
            (filter_date,)
        )
    else:
        rows = query(
            """SELECT a.id, s.name, s.roll_no, a.date, a.time, a.status
               FROM attendance a
               JOIN students s ON s.id = a.student_id
               ORDER BY a.date DESC, a.time DESC
               LIMIT 200"""
        )

    # Convert date/time objects to strings for JSON serialisation
    for r in rows:
        r["date"] = str(r["date"])
        r["time"] = str(r["time"])

    return jsonify({"success": True, "attendance": rows})


@attendance_bp.route("/mark-attendance", methods=["POST"])
def mark_attendance():
    """
    POST /mark-attendance
    Body (JSON):  { "image": "<base64 data-URL>" }

    1. Decodes the image
    2. Runs face recognition
    3. Looks up each recognised roll_no in the DB
    4. Marks attendance (once per day)
    5. Returns list of marked / already-marked / unknown results
    """
    body = request.get_json() or {}
    b64  = body.get("image", "")

    if not b64:
        return jsonify({"success": False, "message": "No image provided"}), 400

    frame = _decode_frame(b64)
    if frame is None:
        return jsonify({"success": False, "message": "Could not decode image"}), 400

    detections = identify_face_from_frame(frame)

    if not detections:
        return jsonify({"success": True, "message": "No faces detected", "results": []})

    today     = date.today().isoformat()
    now_time  = datetime.now().strftime("%H:%M:%S")
    results   = []

    for det in detections:
        roll_no    = det["roll_no"]
        confidence = det["confidence"]

        if roll_no == "Unknown":
            results.append({"roll_no": "Unknown", "status": "unrecognised", "confidence": confidence})
            continue

        student = _student_by_roll(roll_no)
        if not student:
            results.append({"roll_no": roll_no, "status": "not_in_db", "confidence": confidence})
            continue

        if _already_marked(student["id"], today):
            results.append({
                "roll_no": roll_no,
                "name":    student["name"],
                "status":  "already_marked",
                "confidence": confidence
            })
            continue

        execute(
            "INSERT INTO attendance (student_id, date, time, status) VALUES (%s, %s, %s, 'Present')",
            (student["id"], today, now_time)
        )
        results.append({
            "roll_no":    roll_no,
            "name":       student["name"],
            "status":     "marked",
            "confidence": confidence
        })

    # Return an annotated frame thumbnail (optional — used by frontend)
    annotated   = annotate_frame(frame, detections)
    _, buf       = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
    annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode()

    return jsonify({
        "success":        True,
        "results":        results,
        "annotated_frame": annotated_b64
    })


@attendance_bp.route("/attendance/summary", methods=["GET"])
def attendance_summary():
    """GET /attendance/summary  →  count of distinct present students today."""
    today = date.today().isoformat()
    row   = query(
        "SELECT COUNT(*) AS count FROM attendance WHERE date = %s AND status='Present'",
        (today,), fetchone=True
    )
    total = query("SELECT COUNT(*) AS count FROM students", fetchone=True)
    return jsonify({
        "success":        True,
        "date":           today,
        "present_today":  row["count"],
        "total_students": total["count"]
    })
