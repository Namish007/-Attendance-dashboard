# backend/routes/export.py
import csv, io
from flask import Blueprint, request, make_response
from backend.utils.db import query

export_bp = Blueprint("export", __name__)

@export_bp.route("/export/attendance", methods=["GET"])
def export_attendance():
    filter_date  = request.args.get("date", "")
    student_id   = request.args.get("student_id", "")

    if student_id:
        # Individual student CSV
        student = query("SELECT name, roll_no FROM students WHERE id=%s", (student_id,), fetchone=True)
        rows = query(
            """SELECT s.name, s.roll_no, a.date, a.time, a.status
               FROM attendance a JOIN students s ON s.id=a.student_id
               WHERE a.student_id=%s ORDER BY a.date DESC""",
            (student_id,)
        )
        sname    = student["roll_no"] if student else student_id
        filename = f"attendance_{sname}.csv"

    elif filter_date:
        rows = query(
            """SELECT s.name, s.roll_no, a.date, a.time, a.status
               FROM attendance a JOIN students s ON s.id=a.student_id
               WHERE a.date=%s ORDER BY a.time""",
            (filter_date,)
        )
        filename = f"attendance_{filter_date}.csv"

    else:
        rows = query(
            """SELECT s.name, s.roll_no, a.date, a.time, a.status
               FROM attendance a JOIN students s ON s.id=a.student_id
               ORDER BY a.date DESC, a.time DESC"""
        )
        filename = "attendance_all.csv"

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Roll No", "Date", "Time", "Status"])
    for r in rows:
        writer.writerow([r["name"], r["roll_no"], str(r["date"]), str(r["time"]), r["status"]])

    resp = make_response(output.getvalue())
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    resp.headers["Content-Type"] = "text/csv"
    return resp
