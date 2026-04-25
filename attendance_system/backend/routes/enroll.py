# backend/routes/enroll.py
# ─────────────────────────────────────────────────────────────
# Lets the admin capture a student's face directly from the
# browser webcam and save it to the dataset folder.
#
# POST /api/enroll
#   Body: { "roll_no": "...", "image": "<base64 data-URL>" }
#
# After capturing enough photos (3+), run train_faces.py again.
# ─────────────────────────────────────────────────────────────

import os
import base64
import glob
from flask import Blueprint, jsonify, request
from backend.config import DATASET_DIR

enroll_bp = Blueprint("enroll", __name__)


@enroll_bp.route("/enroll", methods=["POST"])
def enroll_student():
    body    = request.get_json() or {}
    roll_no = body.get("roll_no", "").strip()
    b64_img = body.get("image", "")

    if not roll_no:
        return jsonify({"success": False, "message": "roll_no is required"}), 400
    if not b64_img:
        return jsonify({"success": False, "message": "image is required"}), 400

    # Sanitise roll_no (no path traversal)
    roll_no = "".join(c for c in roll_no if c.isalnum() or c in "-_")

    student_dir = os.path.join(DATASET_DIR, roll_no)
    os.makedirs(student_dir, exist_ok=True)

    # Count existing photos to create a sequential filename
    existing = glob.glob(os.path.join(student_dir, "*.jpg"))
    idx      = len(existing) + 1
    filepath = os.path.join(student_dir, f"photo_{idx:03d}.jpg")

    # Decode and save
    try:
        if "," in b64_img:
            b64_img = b64_img.split(",", 1)[1]
        img_bytes = base64.b64decode(b64_img)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to save image: {e}"}), 500

    total = len(glob.glob(os.path.join(student_dir, "*.jpg")))
    return jsonify({
        "success":      True,
        "message":      f"Photo {idx} saved for {roll_no}",
        "total_photos": total,
        "ready":        total >= 3    # suggest retraining when 3+ photos exist
    })


@enroll_bp.route("/enroll/count/<roll_no>", methods=["GET"])
def enroll_count(roll_no):
    """GET /api/enroll/count/<roll_no> — how many photos exist for this student."""
    roll_no = "".join(c for c in roll_no if c.isalnum() or c in "-_")
    student_dir = os.path.join(DATASET_DIR, roll_no)
    total = len(glob.glob(os.path.join(student_dir, "*.jpg"))) if os.path.isdir(student_dir) else 0
    return jsonify({"roll_no": roll_no, "total_photos": total, "ready": total >= 3})
