# backend/utils/recognizer.py
# ─────────────────────────────────────────────────────────────
# Core recognition helper used by the Flask routes.
# Loads encodings once at startup, then reuses them.
# ─────────────────────────────────────────────────────────────

import sys
import pickle
import numpy as np
import face_recognition
import cv2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.config import ENCODING_FILE as _ENC_STR, FACE_TOLERANCE as TOLERANCE, FRAME_SCALE

ENCODING_FILE = Path(_ENC_STR)

_data = None   # cached after first load


def _load():
    global _data
    if _data is None:
        if not ENCODING_FILE.exists():
            raise FileNotFoundError(
                "models/encodings.pkl not found. "
                "Run  python backend/utils/train_faces.py  first."
            )
        with open(ENCODING_FILE, "rb") as f:
            _data = pickle.load(f)
    return _data


def identify_face_from_frame(frame_bgr: np.ndarray) -> list[dict]:
    """
    Given a BGR frame (from OpenCV), detect + recognise all faces.

    Returns a list of dicts:
      [{"roll_no": "...", "confidence": 0.87, "box": (top,right,bottom,left)}, ...]
    Unknown faces have roll_no = "Unknown".
    """
    data = _load()
    rgb  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    # Resize for faster processing (scale = 0.5)
    small     = cv2.resize(rgb, (0, 0), fx=FRAME_SCALE, fy=FRAME_SCALE)
    locations = face_recognition.face_locations(small, model="hog")
    encodings = face_recognition.face_encodings(small, locations)

    results = []
    for enc, loc in zip(encodings, locations):
        top, right, bottom, left = loc

        # Scale boxes back to original size
        scale = int(1 / FRAME_SCALE)
        box = (top * scale, right * scale, bottom * scale, left * scale)

        matches  = face_recognition.compare_faces(
            data["encodings"], enc, tolerance=TOLERANCE
        )
        distances = face_recognition.face_distance(data["encodings"], enc)

        roll_no    = "Unknown"
        confidence = 0.0

        if True in matches:
            best_idx   = int(np.argmin(distances))
            roll_no    = data["roll_nos"][best_idx]
            confidence = round(1 - float(distances[best_idx]), 4)

        results.append({
            "roll_no":    roll_no,
            "confidence": confidence,
            "box":        box      # (top, right, bottom, left)
        })

    return results


def annotate_frame(frame_bgr: np.ndarray, detections: list[dict]) -> np.ndarray:
    """Draw bounding boxes + labels on a copy of the frame."""
    out = frame_bgr.copy()
    for d in detections:
        top, right, bottom, left = d["box"]
        color  = (0, 200, 0) if d["roll_no"] != "Unknown" else (0, 0, 220)
        label  = f"{d['roll_no']}  {d['confidence']*100:.0f}%"
        cv2.rectangle(out, (left, top), (right, bottom), color, 2)
        cv2.rectangle(out, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
        cv2.putText(out, label, (left + 4, bottom - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return out
