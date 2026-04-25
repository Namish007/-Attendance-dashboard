# backend/utils/train_faces.py
# ─────────────────────────────────────────────────────────────
# Run ONCE after adding student photos to dataset/<roll_no>/
# Creates models/encodings.pkl used by the live recogniser.
#
# Usage:
#   cd attendance_system
#   python backend/utils/train_faces.py
# ─────────────────────────────────────────────────────────────

import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pickle
import face_recognition
from pathlib import Path
from backend.config import DATASET_DIR, ENCODING_FILE, MODELS_DIR

os.makedirs(MODELS_DIR, exist_ok=True)


def train():
    known_encodings = []
    known_roll_nos  = []

    dataset_path = Path(DATASET_DIR)
    if not dataset_path.exists():
        print(f"[ERROR] Dataset folder not found: {DATASET_DIR}")
        print("        Create dataset/<roll_no>/ folders with student photos.")
        return

    folders = [f for f in dataset_path.iterdir() if f.is_dir()]
    if not folders:
        print("[WARN] No student folders found in dataset/")
        return

    print(f"[INFO] Processing {len(folders)} student folder(s) …\n")

    for student_dir in sorted(folders):
        roll_no = student_dir.name
        images  = (list(student_dir.glob("*.jpg"))  +
                   list(student_dir.glob("*.jpeg")) +
                   list(student_dir.glob("*.png")))

        if not images:
            print(f"  [SKIP] {roll_no} — no images found")
            continue

        count = 0
        for img_path in images:
            img  = face_recognition.load_image_file(str(img_path))
            encs = face_recognition.face_encodings(img)
            if encs:
                known_encodings.append(encs[0])
                known_roll_nos.append(roll_no)
                count += 1
            else:
                print(f"  [WARN] {roll_no}/{img_path.name} — no face detected, skipping")

        print(f"  [OK]  {roll_no} — {count}/{len(images)} images encoded")

    if not known_encodings:
        print("\n[ERROR] No encodings created. Check that photos contain clear faces.")
        return

    with open(ENCODING_FILE, "wb") as f:
        pickle.dump({"encodings": known_encodings, "roll_nos": known_roll_nos}, f)

    print(f"\n[DONE] {len(known_encodings)} encoding(s) saved → {ENCODING_FILE}")
    print("       Restart the Flask server to load the new model.\n")


if __name__ == "__main__":
    train()
