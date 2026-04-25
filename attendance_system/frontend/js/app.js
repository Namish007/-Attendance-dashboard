// frontend/js/app.js  — Auto-mode + Individual Student Profile
"use strict";
const API = "http://localhost:5000/api";

// ══════════════════════════════════════════════════════════════
//  ROUTING
// ══════════════════════════════════════════════════════════════
const PAGE_TITLES = {
  dashboard: "Dashboard",
  camera:    "Mark Attendance — Auto Mode",
  records:   "Attendance Records",
  students:  "Students",
  profile:   "Student Profile",
  enroll:    "Enroll Student",
  admin:     "Admin",
};

document.querySelectorAll(".nav-item").forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    navigateTo(link.dataset.page);
  });
});

function navigateTo(page) {
  // Stop camera if leaving the camera page
  if (page !== "camera" && _stream) stopCamera();

  document.querySelectorAll(".nav-item").forEach(l => l.classList.remove("active"));
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));

  const link = document.querySelector(`.nav-item[data-page="${page}"]`);
  const pg   = document.getElementById(`page-${page}`);
  if (link) link.classList.add("active");
  if (pg)   pg.classList.add("active");
  document.getElementById("pageTitle").textContent = PAGE_TITLES[page] || page;

  if (page === "dashboard") loadDashboard();
  if (page === "records")   loadAttendanceRecords();
  if (page === "students")  loadStudents();
  if (page === "admin")     loadAdminStats();
}

// ══════════════════════════════════════════════════════════════
//  CLOCK
// ══════════════════════════════════════════════════════════════
function updateClock() {
  const now = new Date();
  document.getElementById("liveClock").textContent =
    now.toLocaleDateString("en-IN", { weekday:"long", year:"numeric", month:"long", day:"numeric" }) +
    "  " + now.toLocaleTimeString("en-IN");
}
setInterval(updateClock, 1000);
updateClock();

// ══════════════════════════════════════════════════════════════
//  SERVER STATUS
// ══════════════════════════════════════════════════════════════
async function checkServer() {
  const dot  = document.getElementById("serverStatus");
  const text = document.getElementById("serverStatusText");
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) { dot.className = "status-dot online";  text.textContent = "Server online";  return; }
  } catch (_) {}
  dot.className = "status-dot offline"; text.textContent = "Server offline";
}
setInterval(checkServer, 8000);
checkServer();

// ══════════════════════════════════════════════════════════════
//  TOAST
// ══════════════════════════════════════════════════════════════
let _toastTimer;
function toast(msg, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast show" + (isError ? " error" : "");
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove("show"), 3500);
}

// ══════════════════════════════════════════════════════════════
//  DASHBOARD
// ══════════════════════════════════════════════════════════════
async function loadDashboard() {
  await Promise.all([loadSummary(), loadTodayAttendance()]);
}

async function loadSummary() {
  try {
    const r   = await fetch(`${API}/attendance/summary`);
    const d   = await r.json();
    const pct = d.total_students > 0
      ? Math.round((d.present_today / d.total_students) * 100) : 0;
    document.getElementById("statPresent").textContent = d.present_today;
    document.getElementById("statTotal").textContent   = d.total_students;
    document.getElementById("statAbsent").textContent  = d.total_students - d.present_today;
    document.getElementById("statPct").textContent     = pct + "%";
  } catch (_) { toast("Cannot load — is the server running?", true); }
}

async function loadTodayAttendance() {
  const today = new Date().toISOString().split("T")[0];
  try {
    const r     = await fetch(`${API}/attendance?date=${today}`);
    const d     = await r.json();
    const tbody = document.getElementById("dashTableBody");
    if (!d.attendance?.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-row">No attendance recorded today yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = d.attendance.map((row, i) => `
      <tr>
        <td>${i+1}</td>
        <td>${esc(row.name)}</td>
        <td><code>${esc(row.roll_no)}</code></td>
        <td>${row.time}</td>
        <td><span class="badge badge--present">${row.status}</span></td>
      </tr>`).join("");
  } catch(e) { console.error(e); }
}

function exportToday() {
  const today = new Date().toISOString().split("T")[0];
  window.location = `${API}/export/attendance?date=${today}`;
}

// ══════════════════════════════════════════════════════════════
//  AUTO-MODE CAMERA  ← THE NEW FEATURE
//  Camera opens → automatically scans every N seconds
//  No capture button needed
// ══════════════════════════════════════════════════════════════
let _stream        = null;
let _autoTimer     = null;
let _timerCountdown= null;
let _scanning      = false;
let _sessionMarked = {};   // roll_no → name  (marked this session)
let _countdown     = 0;

async function startCamera() {
  try {
    _stream = await navigator.mediaDevices.getUserMedia({
      video: { width:640, height:480, facingMode:"user" }
    });

    const video = document.getElementById("webcam");
    video.srcObject = _stream;
    video.style.display = "block";

    const canvas = document.getElementById("overlayCanvas");
    canvas.width  = 640; canvas.height = 480;
    canvas.style.display = "block";

    document.getElementById("cameraOverlay").classList.add("hidden");
    document.getElementById("camStatusBar").style.display = "flex";
    document.getElementById("btnStartCam").disabled = true;
    document.getElementById("btnStopCam").disabled  = false;

    document.getElementById("liveLog").innerHTML = "";
    _sessionMarked = {};

    // ── Start automatic scanning ──
    _startAutoScan();

    toast("Camera started — Auto scanning active");
  } catch (_) {
    toast("Camera access denied. Allow camera in browser.", true);
  }
}

function _startAutoScan() {
  const interval = parseInt(document.getElementById("scanInterval").value) || 3000;
  _countdown = Math.round(interval / 1000);

  // Countdown timer display
  _updateCountdownDisplay(_countdown);
  _timerCountdown = setInterval(() => {
    _countdown--;
    if (_countdown <= 0) _countdown = Math.round(interval / 1000);
    _updateCountdownDisplay(_countdown);
  }, 1000);

  // Auto-scan at chosen interval
  _autoTimer = setInterval(() => {
    if (!_scanning) _doAutoScan();
  }, interval);

  // First scan immediately after 1s
  setTimeout(() => { if (!_scanning) _doAutoScan(); }, 1000);
}

function _updateCountdownDisplay(n) {
  const el = document.getElementById("camTimer");
  if (el) { el.textContent = n + "s"; }
}

async function _doAutoScan() {
  if (!_stream) return;
  _scanning = true;

  const video  = document.getElementById("webcam");
  const canvas = document.getElementById("snapshot");
  canvas.width  = video.videoWidth  || 640;
  canvas.height = video.videoHeight || 480;
  canvas.getContext("2d").drawImage(video, 0, 0);
  const b64 = canvas.toDataURL("image/jpeg", 0.80);

  document.getElementById("camStatusText").textContent = "Scanning faces…";

  try {
    const r = await fetch(`${API}/mark-attendance`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ image: b64 }),
    });
    const d = await r.json();

    if (d.results && d.results.length > 0) {
      // Draw bounding boxes on overlay canvas
      if (d.annotated_frame) _flashAnnotated(d.annotated_frame);

      d.results.forEach(res => _addLogEntry(res));
      loadSummary();
    } else {
      document.getElementById("camStatusText").textContent = "No face detected — keep looking…";
    }
  } catch (e) {
    document.getElementById("camStatusText").textContent = "Scan error — retrying…";
    console.error(e);
  }

  _scanning = false;
}

function _addLogEntry(res) {
  const log  = document.getElementById("liveLog");
  const now  = new Date().toLocaleTimeString("en-IN");
  let cls, icon, nameText;

  if (res.status === "marked") {
    cls = "log-marked"; icon = "✔";
    nameText = res.name || res.roll_no;
    _sessionMarked[res.roll_no] = res.name;
    _updateSessionSummary();
    document.getElementById("camStatusText").textContent = `✔ ${res.name} marked present`;
    toast(`✔ ${res.name} — Attendance Marked!`);
  } else if (res.status === "already_marked") {
    cls = "log-already"; icon = "⚠";
    nameText = res.name || res.roll_no;
    document.getElementById("camStatusText").textContent = `${res.name} already marked today`;
  } else {
    cls = "log-unknown"; icon = "✖";
    nameText = "Unknown Face";
    document.getElementById("camStatusText").textContent = "Unknown face detected";
  }

  const entry = document.createElement("div");
  entry.className = `log-entry ${cls}`;
  entry.innerHTML = `
    <span class="log-time">${now}</span>
    <div>
      <div class="log-name">${icon} ${esc(nameText)}</div>
      <div class="log-roll">${esc(res.roll_no)} · ${Math.round((res.confidence||0)*100)}% confidence</div>
    </div>`;

  // Prepend (newest on top)
  log.insertBefore(entry, log.firstChild);

  // Trim to last 30 entries
  while (log.children.length > 30) log.removeChild(log.lastChild);
}

function _updateSessionSummary() {
  const box = document.getElementById("sessionBox");
  const summary = document.getElementById("sessionSummary");
  const names = Object.values(_sessionMarked);
  box.style.display = "block";
  summary.innerHTML = names.map(n =>
    `<div class="session-item">✔ ${esc(n)}</div>`
  ).join("") + `<div style="margin-top:6px;font-size:11px;color:var(--muted)">${names.length} student(s) marked this session</div>`;
}

function _flashAnnotated(b64) {
  // Show annotated frame briefly on the video overlay using canvas
  const canvas = document.getElementById("overlayCanvas");
  const ctx = canvas.getContext("2d");
  const img = new Image();
  img.onload = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    setTimeout(() => ctx.clearRect(0, 0, canvas.width, canvas.height), 1500);
  };
  img.src = b64;
}

function stopCamera() {
  clearInterval(_autoTimer);    _autoTimer      = null;
  clearInterval(_timerCountdown); _timerCountdown = null;
  _scanning = false;

  if (_stream) { _stream.getTracks().forEach(t => t.stop()); _stream = null; }

  const video = document.getElementById("webcam");
  video.srcObject = null; video.style.display = "none";

  const canvas = document.getElementById("overlayCanvas");
  canvas.style.display = "none";

  document.getElementById("cameraOverlay").classList.remove("hidden");
  document.getElementById("camStatusBar").style.display = "none";
  document.getElementById("btnStartCam").disabled = false;
  document.getElementById("btnStopCam").disabled  = true;

  toast("Camera stopped");
}

// ══════════════════════════════════════════════════════════════
//  RECORDS
// ══════════════════════════════════════════════════════════════
async function loadAttendanceRecords() {
  const dateVal = document.getElementById("filterDate").value;
  const url     = dateVal ? `${API}/attendance?date=${dateVal}` : `${API}/attendance`;
  try {
    const r     = await fetch(url);
    const d     = await r.json();
    const tbody = document.getElementById("recordsBody");
    if (!d.attendance?.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-row">No records found.</td></tr>`; return;
    }
    tbody.innerHTML = d.attendance.map((row, i) => `
      <tr>
        <td>${i+1}</td>
        <td>${esc(row.name)}</td>
        <td><code>${esc(row.roll_no)}</code></td>
        <td>${row.date}</td>
        <td>${row.time}</td>
        <td><span class="badge badge--present">${row.status}</span></td>
      </tr>`).join("");
  } catch (_) { toast("Failed to load records.", true); }
}

function clearDateFilter() {
  document.getElementById("filterDate").value = "";
  loadAttendanceRecords();
}
function exportRecords() {
  const dateVal = document.getElementById("filterDate").value;
  window.location = dateVal
    ? `${API}/export/attendance?date=${dateVal}`
    : `${API}/export/attendance`;
}

// ══════════════════════════════════════════════════════════════
//  STUDENTS LIST  — with individual stats per row
// ══════════════════════════════════════════════════════════════
let _allStudents = [];

async function loadStudents() {
  try {
    const r = await fetch(`${API}/students`);
    const d = await r.json();
    _allStudents = d.students || [];
    const tbody = document.getElementById("studentsBody");

    if (!_allStudents.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-row">No students enrolled.</td></tr>`; return;
    }

    // Load stats for each student
    const statsArr = await Promise.all(
      _allStudents.map(s => fetchStudentStats(s.id))
    );

    tbody.innerHTML = _allStudents.map((s, i) => {
      const stats = statsArr[i];
      const pct   = stats ? stats.percentage : 0;
      const pctClass = pct >= 75 ? "pct-high" : pct >= 50 ? "pct-medium" : "pct-low";
      const lastSeen = stats ? stats.last_seen : "—";
      const present  = stats ? stats.total_present : "—";
      return `
        <tr>
          <td>${i+1}</td>
          <td>${esc(s.name)}</td>
          <td><code>${esc(s.roll_no)}</code></td>
          <td>${present}</td>
          <td><span class="${pctClass}">${pct}%</span></td>
          <td>${lastSeen}</td>
          <td><button class="view-btn" onclick="openProfile(${s.id})">View Profile</button></td>
        </tr>`;
    }).join("");
  } catch (_) { toast("Failed to load students.", true); }
}

async function fetchStudentStats(studentId) {
  try {
    const r = await fetch(`${API}/students/${studentId}/attendance`);
    const d = await r.json();
    return d.success ? d.stats : null;
  } catch (_) { return null; }
}

function toggleAddForm() {
  const f = document.getElementById("addForm");
  f.style.display = f.style.display === "none" ? "block" : "none";
}

async function addStudent() {
  const name    = document.getElementById("newName").value.trim();
  const roll_no = document.getElementById("newRoll").value.trim();
  if (!name || !roll_no) { toast("Name and Roll No are required.", true); return; }
  try {
    const r = await fetch(`${API}/students`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, roll_no }),
    });
    const d = await r.json();
    if (d.success) {
      toast(`✔ ${name} added`);
      document.getElementById("newName").value = "";
      document.getElementById("newRoll").value = "";
      loadStudents();
    } else { toast(d.message || "Failed.", true); }
  } catch (_) { toast("Server error.", true); }
}

// ══════════════════════════════════════════════════════════════
//  INDIVIDUAL STUDENT PROFILE  ← THE NEW FEATURE
// ══════════════════════════════════════════════════════════════
let _currentProfileId = null;

async function openProfile(studentId) {
  _currentProfileId = studentId;
  navigateTo("profile");

  // Reset
  document.getElementById("profileName").textContent    = "Loading…";
  document.getElementById("profileRoll").textContent    = "";
  document.getElementById("profilePresent").textContent = "—";
  document.getElementById("profileWorking").textContent = "—";
  document.getElementById("profilePct").textContent     = "—";
  document.getElementById("profileLastSeen").textContent = "—";
  document.getElementById("profilePctBar").style.width  = "0%";

  try {
    const r = await fetch(`${API}/students/${studentId}/attendance`);
    const d = await r.json();
    if (!d.success) { toast("Could not load student data.", true); return; }

    const { student, stats, monthly, attendance } = d;

    // Header
    document.getElementById("profileName").textContent   = student.name;
    document.getElementById("profileRoll").textContent   = `Roll No: ${student.roll_no}`;
    document.getElementById("profileAvatar").textContent = student.name.charAt(0).toUpperCase();

    // Stats
    document.getElementById("profilePresent").textContent  = stats.total_present;
    document.getElementById("profileWorking").textContent  = stats.total_working_days;
    document.getElementById("profilePct").textContent      = stats.percentage + "%";
    document.getElementById("profileLastSeen").textContent = stats.last_seen;

    // Progress bar
    const pct = Math.min(stats.percentage, 100);
    document.getElementById("profilePctBar").style.width = pct + "%";
    document.getElementById("profilePctLabel").textContent = pct + "%";

    // Color the percentage
    const pctEl = document.getElementById("profilePct");
    pctEl.className = "stat-value " + (pct >= 75 ? "pct-high" : pct >= 50 ? "pct-medium" : "pct-low");

    // Monthly breakdown table
    const monthlyBody = document.getElementById("profileMonthly");
    if (!monthly.length) {
      monthlyBody.innerHTML = `<tr><td colspan="2" class="empty-row">No data yet</td></tr>`;
    } else {
      monthlyBody.innerHTML = monthly.map(m => `
        <tr>
          <td>${formatMonth(m.month)}</td>
          <td><strong>${m.present_days}</strong> days</td>
        </tr>`).join("");
    }

    // Full attendance history
    const historyBody = document.getElementById("profileHistory");
    if (!attendance.length) {
      historyBody.innerHTML = `<tr><td colspan="5" class="empty-row">No attendance records yet</td></tr>`;
    } else {
      historyBody.innerHTML = attendance.map((row, i) => {
        const dateObj = new Date(row.date);
        const dayName = dateObj.toLocaleDateString("en-IN", { weekday: "long" });
        return `
          <tr>
            <td>${i+1}</td>
            <td>${row.date}</td>
            <td class="day-name">${dayName}</td>
            <td>${row.time}</td>
            <td><span class="badge badge--present">${row.status}</span></td>
          </tr>`;
      }).join("");
    }

  } catch (e) {
    toast("Error loading profile.", true); console.error(e);
  }
}

function formatMonth(ym) {
  // "2025-01" → "January 2025"
  const [y, m] = ym.split("-");
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[parseInt(m)-1]} ${y}`;
}

function exportStudentCSV() {
  if (_currentProfileId) {
    // Export all attendance filtered by opening student profile
    // Re-uses general export with student_id param
    toast("Downloading CSV…");
    window.location = `${API}/export/attendance?student_id=${_currentProfileId}`;
  }
}

// ══════════════════════════════════════════════════════════════
//  ENROLL
// ══════════════════════════════════════════════════════════════
let _enrollStream = null;
let _enrollCount  = 0;

async function startEnrollCam() {
  try {
    _enrollStream = await navigator.mediaDevices.getUserMedia({ video:{width:640,height:480} });
    const v = document.getElementById("enrollWebcam");
    v.srcObject = _enrollStream; v.style.display = "block";
    document.getElementById("enrollOverlay").classList.add("hidden");
    document.getElementById("enrollPreview").style.display = "none";
    document.getElementById("btnEnrollStart").disabled = true;
    document.getElementById("btnEnrollStop").disabled  = false;
    document.getElementById("btnEnrollSnap").disabled  = false;

    const roll = document.getElementById("enrollRoll").value.trim();
    if (roll) {
      const r = await fetch(`${API}/enroll/count/${roll}`);
      const d = await r.json();
      _enrollCount = d.total_photos;
      updateEnrollStatus(_enrollCount);
    }
  } catch (_) { toast("Camera access denied.", true); }
}

function stopEnrollCam() {
  if (_enrollStream) { _enrollStream.getTracks().forEach(t=>t.stop()); _enrollStream=null; }
  const v = document.getElementById("enrollWebcam");
  v.srcObject=null; v.style.display="none";
  document.getElementById("enrollOverlay").classList.remove("hidden");
  document.getElementById("btnEnrollStart").disabled=false;
  document.getElementById("btnEnrollStop").disabled=true;
  document.getElementById("btnEnrollSnap").disabled=true;
}

async function enrollSnap() {
  const roll = document.getElementById("enrollRoll").value.trim();
  if (!roll) { toast("Enter roll number first.", true); return; }

  const video = document.getElementById("enrollWebcam");
  const canvas = document.getElementById("enrollCanvas");
  canvas.width = video.videoWidth||640; canvas.height = video.videoHeight||480;
  canvas.getContext("2d").drawImage(video,0,0);
  const b64 = canvas.toDataURL("image/jpeg",0.92);

  const prev = document.getElementById("enrollPreview");
  prev.src=b64; prev.style.display="block"; video.style.display="none";
  setTimeout(()=>{ prev.style.display="none"; video.style.display="block"; },700);

  try {
    const r = await fetch(`${API}/enroll`,{
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ roll_no:roll, image:b64 }),
    });
    const d = await r.json();
    if (d.success) {
      _enrollCount = d.total_photos;
      updateEnrollStatus(_enrollCount);
      if (d.ready) toast(`✔ ${_enrollCount} photos — go to Admin → Retrain!`);
      else toast(`Photo ${_enrollCount} saved`);
    } else { toast(d.message||"Save failed.",true); }
  } catch (_) { toast("Server error.",true); }
}

function updateEnrollStatus(count) {
  const TARGET = 5;
  const dots = Array.from({length:TARGET},(_,i)=>
    `<div class="photo-dot ${i<count?"filled":""}"></div>`).join("");
  const msg = count>=TARGET
    ? `<span style="color:var(--green);font-weight:700">✔ ${count} photos — Admin → Retrain now</span>`
    : `<span style="color:var(--muted)">${count}/${TARGET} photos captured</span>`;
  document.getElementById("enrollStatus").innerHTML=
    `<div class="photo-bar">${dots}</div><p style="margin-top:8px;font-size:12px">${msg}</p>`;
}

// ══════════════════════════════════════════════════════════════
//  ADMIN
// ══════════════════════════════════════════════════════════════
async function loadAdminStats() {
  try {
    const r = await fetch(`${API}/admin/stats`);
    const d = await r.json();
    document.getElementById("adminStats").innerHTML = `
      <ul class="stats-list">
        <li><span>Total students</span>         <span class="s-val">${d.total_students}</span></li>
        <li><span>Total attendance rows</span>  <span class="s-val">${d.total_attendance_rows}</span></li>
        <li><span>Present today</span>          <span class="s-val">${d.present_today}</span></li>
      </ul>`;
  } catch (_) {
    document.getElementById("adminStats").innerHTML=`<p class="empty-hint">Could not load stats.</p>`;
  }
}

async function retrain() {
  const btn = document.getElementById("btnRetrain");
  const log = document.getElementById("retrainLog");
  btn.disabled=true; btn.textContent="⏳ Training…";
  log.style.display="block"; log.textContent="Starting face encoding…\n";
  try {
    const r = await fetch(`${API}/admin/retrain`,{method:"POST"});
    const d = await r.json();
    log.textContent = d.output || d.message || "(no output)";
    if (d.success) toast("✔ Retraining complete! Restart Flask server.");
    else toast("Retraining failed — see log.",true);
  } catch (_) {
    log.textContent="Network error — is the server running?";
    toast("Server error.",true);
  } finally { btn.disabled=false; btn.textContent="Start Retraining"; }
}

// ══════════════════════════════════════════════════════════════
//  UTILITIES
// ══════════════════════════════════════════════════════════════
function esc(s) {
  return String(s??"")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ══════════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════════
loadDashboard();
