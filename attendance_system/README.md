# AI-Based Smart Classroom Attendance System
### NIET Greater Noida — B.Tech CSE Project

---

## 📁 Folder Structure

```
attendance_system/
├── frontend/
│   ├── index.html          ← Main UI (dashboard, camera, records, students)
│   ├── css/style.css       ← All styles
│   └── js/app.js           ← All frontend logic + API calls
│
├── backend/
│   ├── app.py              ← Flask entry point (run this!)
│   ├── routes/
│   │   ├── students.py     ← GET/POST /api/students
│   │   └── attendance.py   ← POST /api/mark-attendance, GET /api/attendance
│   └── utils/
│       ├── db.py           ← MySQL connection helper
│       ├── recognizer.py   ← Face detection + recognition logic
│       └── train_faces.py  ← Script to encode student faces (run once)
│
├── database/
│   └── attendance_system.sql  ← MySQL schema + sample data
│
├── dataset/                ← Put student photos here (see below)
│   └── <roll_no>/
│       ├── photo1.jpg
│       └── photo2.jpg
│
├── models/
│   └── encodings.pkl       ← Auto-generated after training
│
└── requirements.txt
```

---

## ⚙️ Step-by-Step Setup

### 1. Install Python 3.10+
Download from https://python.org and make sure `python` is in your PATH.

### 2. Install CMake (required for dlib/face_recognition)
**Windows:** Download from https://cmake.org/download/ — check "Add to PATH"
**Ubuntu/Mac:** `sudo apt install cmake` or `brew install cmake`

### 3. Install Visual C++ Build Tools (Windows only)
Download "Build Tools for Visual Studio" from:
https://visualstudio.microsoft.com/visual-cpp-build-tools/
Select "C++ build tools" workload.

### 4. Install Python dependencies
Open a terminal in the `attendance_system/` folder:
```bash
pip install -r requirements.txt
```
> ⚠️ `dlib` and `face_recognition` can take 5-15 minutes to build.

### 5. Set up MySQL via XAMPP
1. Download & install XAMPP from https://www.apachefriends.org/
2. Open XAMPP Control Panel → Start **Apache** and **MySQL**
3. Open your browser → go to `http://localhost/phpmyadmin`
4. Click **"New"** in the left panel → name it `attendance_system` → click **Create**
5. Click the new database → click **Import** tab
6. Choose file: `database/attendance_system.sql` → click **Go**
7. You should see tables `students` and `attendance` created with sample data.

### 6. Add student photos for training
For each student, create a folder named by their roll number inside `dataset/`:
```
dataset/
  2401330100295/
    front.jpg
    side.jpg
  2401330100231/
    photo1.jpg
```
> Each student needs at least 3-5 clear photos. Make sure the face is visible.

### 7. Train the face recognition model
```bash
python backend/utils/train_faces.py
```
This creates `models/encodings.pkl`. Re-run whenever you add new students.

### 8. Start the Flask server
```bash
python backend/app.py
```
You should see:
```
=======================================================
  AI-Based Smart Attendance System
  Server → http://localhost:5000
=======================================================
```

### 9. Open the frontend
Open your browser and go to: **http://localhost:5000**

---

## 🎯 How to Use

| Feature | Instructions |
|---------|-------------|
| **Dashboard** | See today's summary stats and attendance table |
| **Mark Attendance** | Click "Start Camera" → point camera at students → click "Capture & Mark Attendance" |
| **Records** | Filter attendance by date, or view all records |
| **Students** | View enrolled students, add new ones |

---

## 🔧 Configuration

Edit `backend/utils/db.py` to change database credentials:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",       # your MySQL username
    "password": "",           # your MySQL password
    "database": "attendance_system"
}
```

Adjust recognition sensitivity in `backend/utils/recognizer.py`:
```python
TOLERANCE = 0.50  # Lower = stricter (0.4 strict, 0.6 lenient)
```

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `face_recognition` install fails | Install cmake and Visual C++ build tools first |
| `FileNotFoundError: encodings.pkl` | Run `python backend/utils/train_faces.py` |
| `Cannot connect to MySQL` | Start MySQL in XAMPP Control Panel |
| Camera not working | Allow camera permissions in browser |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |

---

## 🚀 Future Improvements
- Auto-capture every N seconds (continuous monitoring)
- Email/SMS alerts for absent students
- Export attendance to Excel/PDF
- Emotion/engagement detection with MediaPipe
- Multi-camera support
