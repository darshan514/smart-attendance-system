from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import csv
from io import StringIO
import glob
from functools import wraps
from datetime import datetime
import random
import string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "dataset")
TRAINER_PATH = os.path.join(BASE_DIR, "trainer", "trainer.yml")
DB_PATH = os.path.join(BASE_DIR, "attendance.db")
ALLOWED_EXT = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.secret_key = "smart-attendance-secret-key-2025"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "trainer"), exist_ok=True)

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with user tables"""
    conn = get_db_conn()
    c = conn.cursor()
    
    # Users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # OTP Verification table (for multi-step registration)
    c.execute('''
    CREATE TABLE IF NOT EXISTS otp_verification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_or_email TEXT UNIQUE NOT NULL,
        otp TEXT NOT NULL,
        method TEXT NOT NULL,
        verification_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    )
    ''')
    
    # Students table (updated)
    c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        encoding BLOB,
        phone TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Attendance table
    c.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        name TEXT,
        timestamp TEXT,
        status TEXT DEFAULT 'present',
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "error")
            return redirect(url_for('login'))
        
        conn = get_db_conn()
        user = conn.execute("SELECT role FROM users WHERE id=?", (session['user_id'],)).fetchone()
        conn.close()
        
        if not user or user['role'] != 'teacher':
            flash("Access denied. Teacher privileges required.", "error")
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# ===== Authentication Routes =====
@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "student")
        
        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for('login'))
        
        conn = get_db_conn()
        user = conn.execute(
            "SELECT id, email, password, role, full_name FROM users WHERE email=? AND role=?",
            (email, role)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "error")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register_user():
    """Step 1: Choose registration method"""
    if request.method == "POST":
        method = request.form.get("method", "").strip()
        
        if method == "phone":
            return redirect(url_for('register_phone'))
        elif method == "google":
            return redirect(url_for('register_google'))
        else:
            flash("Please select a registration method.", "error")
    
    return render_template("register_step1.html")

@app.route("/register/phone", methods=["GET", "POST"])
def register_phone():
    """Step 2: Phone-based registration with OTP"""
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        
        if not phone or len(phone) < 10:
            flash("Please enter a valid phone number.", "error")
            return render_template("register_phone.html")
        
        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Save OTP to database
        conn = get_db_conn()
        try:
            # Check if phone already registered
            existing = conn.execute("SELECT id FROM users WHERE phone=?", (phone,)).fetchone()
            if existing:
                flash("This phone number is already registered.", "error")
                conn.close()
                return render_template("register_phone.html")
            
            # Clear any existing OTP for this phone
            conn.execute("DELETE FROM otp_verification WHERE phone_or_email=?", (phone,))
            
            # Insert new OTP
            conn.execute(
                "INSERT INTO otp_verification (phone_or_email, otp, method) VALUES (?, ?, ?)",
                (phone, otp, "phone")
            )
            conn.commit()
            conn.close()
            
            # In production, send actual SMS via Twilio/AWS SNS
            # For demo, we'll show the OTP (should be removed in production)
            flash(f"OTP sent to {phone}! (Demo OTP: {otp})", "info")
            return redirect(url_for('register_verify_otp', phone_or_email=phone))
            
        except Exception as e:
            conn.close()
            flash(f"Error: {str(e)}", "error")
            return render_template("register_phone.html")
    
    return render_template("register_phone.html")

@app.route("/register/google", methods=["GET", "POST"])
def register_google():
    """Step 2: Google-based registration with OTP"""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email or "@" not in email:
            flash("Please enter a valid email address.", "error")
            return render_template("register_google.html")
        
        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Save OTP to database
        conn = get_db_conn()
        try:
            # Check if email already registered
            existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if existing:
                flash("This email is already registered.", "error")
                conn.close()
                return render_template("register_google.html")
            
            # Clear any existing OTP for this email
            conn.execute("DELETE FROM otp_verification WHERE phone_or_email=?", (email,))
            
            # Insert new OTP
            conn.execute(
                "INSERT INTO otp_verification (phone_or_email, otp, method) VALUES (?, ?, ?)",
                (email, otp, "google")
            )
            conn.commit()
            conn.close()
            
            # In production, send actual email via SendGrid/AWS SES
            # For demo, we'll show the OTP (should be removed in production)
            flash(f"OTP sent to {email}! (Demo OTP: {otp})", "info")
            return redirect(url_for('register_verify_otp', phone_or_email=email))
            
        except Exception as e:
            conn.close()
            flash(f"Error: {str(e)}", "error")
            return render_template("register_google.html")
    
    return render_template("register_google.html")

@app.route("/register/verify-otp", methods=["GET", "POST"])
def register_verify_otp():
    """Step 3: Verify OTP"""
    phone_or_email = request.args.get("phone_or_email", "").strip()
    
    if not phone_or_email:
        flash("Invalid request. Please start registration again.", "error")
        return redirect(url_for('register_user'))
    
    if request.method == "POST":
        otp_code = request.form.get("otp", "").strip()
        
        conn = get_db_conn()
        verification = conn.execute(
            "SELECT * FROM otp_verification WHERE phone_or_email=?",
            (phone_or_email,)
        ).fetchone()
        conn.close()
        
        if not verification:
            flash("OTP expired or not found. Please try again.", "error")
            return redirect(url_for('register_user'))
        
        if verification['otp'] != otp_code:
            flash("Invalid OTP. Please try again.", "error")
            return render_template("register_verify_otp.html", phone_or_email=phone_or_email)
        
        # OTP verified, proceed to details form
        session['verified_contact'] = phone_or_email
        session['verification_method'] = verification['method']
        return redirect(url_for('register_details'))
    
    return render_template("register_verify_otp.html", phone_or_email=phone_or_email)

@app.route("/register/details", methods=["GET", "POST"])
def register_details():
    """Step 4: Collect user details after OTP verification"""
    if 'verified_contact' not in session:
        flash("Please complete OTP verification first.", "error")
        return redirect(url_for('register_user'))
    
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        role = request.form.get("role", "student")
        
        if not all([full_name, password, confirm_password]):
            flash("All fields are required.", "error")
            return render_template("register_details.html", role=role)
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register_details.html", role=role)
        
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register_details.html", role=role)
        
        contact = session.get('verified_contact')
        method = session.get('verification_method')
        
        conn = get_db_conn()
        try:
            hashed_password = generate_password_hash(password)
            
            if method == "phone":
                conn.execute(
                    "INSERT INTO users (email, password, full_name, role, phone) VALUES (?, ?, ?, ?, ?)",
                    (f"user_{contact}@smartattendance.local", hashed_password, full_name, role, contact)
                )
            else:  # google
                conn.execute(
                    "INSERT INTO users (email, password, full_name, role, phone) VALUES (?, ?, ?, ?, ?)",
                    (contact, hashed_password, full_name, role, "")
                )
            
            conn.commit()
            
            # Clean up OTP verification
            conn.execute("DELETE FROM otp_verification WHERE phone_or_email=?", (contact,))
            conn.commit()
            conn.close()
            
            # Clear session
            session.pop('verified_contact', None)
            session.pop('verification_method', None)
            
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
            
        except Exception as e:
            conn.close()
            flash(f"Registration failed: {str(e)}", "error")
            return render_template("register_details.html", role=role)
    
    return render_template("register_details.html", role="student")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# ===== Dashboard Routes =====
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_conn()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    
    if user['role'] == 'teacher':
        students_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        attendance_count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        conn.close()
        return render_template("teacher_dashboard.html", 
                             user=user,
                             students_count=students_count, 
                             attendance_count=attendance_count,
                             trainer_exists=os.path.exists(TRAINER_PATH))
    else:
        student = conn.execute("SELECT * FROM students WHERE user_id=?", (session['user_id'],)).fetchone()
        if student:
            attendance_count = conn.execute("SELECT COUNT(*) FROM attendance WHERE student_id=?", (student['id'],)).fetchone()[0]
            recent_attendance = conn.execute(
                "SELECT timestamp FROM attendance WHERE student_id=? ORDER BY timestamp DESC LIMIT 5",
                (student['id'],)
            ).fetchall()
        else:
            attendance_count = 0
            recent_attendance = []
        conn.close()
        
        return render_template("student_dashboard.html", 
                             user=user,
                             student=student,
                             attendance_count=attendance_count,
                             recent_attendance=recent_attendance)

# ===== Profile Routes =====
@app.route("/profile")
@login_required
def profile():
    conn = get_db_conn()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    student = None
    if user['role'] == 'student':
        student = conn.execute("SELECT * FROM students WHERE user_id=?", (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template("profile.html", user=user, student=student)

@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        
        if not full_name:
            flash("Full name is required.", "error")
            return redirect(url_for('edit_profile'))
        
        conn = get_db_conn()
        conn.execute(
            "UPDATE users SET full_name=?, phone=? WHERE id=?",
            (full_name, phone, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        session['full_name'] = full_name
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))
    
    conn = get_db_conn()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template("edit_profile.html", user=user)

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        if not all([current_password, new_password, confirm_password]):
            flash("All fields are required.", "error")
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for('change_password'))
        
        if len(new_password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for('change_password'))
        
        conn = get_db_conn()
        user = conn.execute("SELECT password FROM users WHERE id=?", (session['user_id'],)).fetchone()
        
        if not check_password_hash(user['password'], current_password):
            flash("Current password is incorrect.", "error")
            conn.close()
            return redirect(url_for('change_password'))
        
        hashed_password = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password=? WHERE id=?", (hashed_password, session['user_id']))
        conn.commit()
        conn.close()
        
        flash("Password changed successfully!", "success")
        return redirect(url_for('profile'))
    
    return render_template("change_password.html")

# ===== Teacher Routes =====
@app.route("/students")
@teacher_required
def students():
    search = request.args.get("search", "").strip()
    conn = get_db_conn()
    if search:
        query = "SELECT id, name, email, phone FROM students WHERE LOWER(name) LIKE ? OR LOWER(email) LIKE ? ORDER BY id"
        rows = conn.execute(query, (f"%{search.lower()}%", f"%{search.lower()}%")).fetchall()
    else:
        rows = conn.execute("SELECT id, name, email, phone FROM students ORDER BY id").fetchall()
    conn.close()
    return render_template("students.html", students=rows, search=search)

@app.route("/attendance")
@teacher_required
def attendance():
    search = request.args.get("search", "").strip()
    conn = get_db_conn()
    if search:
        query = "SELECT id, student_id, name, timestamp FROM attendance WHERE LOWER(name) LIKE ? OR CAST(student_id AS TEXT) LIKE ? ORDER BY timestamp DESC"
        rows = conn.execute(query, (f"%{search.lower()}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute("SELECT id, student_id, name, timestamp FROM attendance ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("attendance.html", attendance=rows, search=search)

@app.route("/student/<int:student_id>")
@teacher_required
def student_detail(student_id):
    conn = get_db_conn()
    student = conn.execute("SELECT id, name, email, phone FROM students WHERE id=?", (student_id,)).fetchone()
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('students'))
    
    attendance_records = conn.execute(
        "SELECT timestamp FROM attendance WHERE student_id=? ORDER BY timestamp DESC LIMIT 10",
        (student_id,)
    ).fetchall()
    total_attendance = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE student_id=?",
        (student_id,)
    ).fetchone()[0]
    conn.close()
    
    return render_template("student_detail.html", student=student, attendance=attendance_records, total=total_attendance)

@app.route("/delete_student/<int:student_id>", methods=["POST"])
@teacher_required
def delete_student(student_id):
    conn = get_db_conn()
    cur = conn.cursor()
    
    student = cur.execute("SELECT name FROM students WHERE id=?", (student_id,)).fetchone()
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('students'))
    
    cur.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
    cur.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()
    
    for file in glob.glob(os.path.join(UPLOAD_FOLDER, f"*.{student_id}.*")):
        try:
            os.remove(file)
        except:
            pass
    
    flash(f"Student {student['name']} deleted successfully.", "success")
    return redirect(url_for('students'))

@app.route("/export_csv")
@teacher_required
def export_csv():
    conn = get_db_conn()
    rows = conn.execute("SELECT student_id, name, timestamp FROM attendance ORDER BY timestamp").fetchall()
    conn.close()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["student_id", "name", "timestamp"])
    for r in rows:
        writer.writerow([r["student_id"], r["name"], r["timestamp"]])
    mem = StringIO(si.getvalue())
    mem.seek(0)
    return send_file(
        path_or_file=mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="attendance_export.csv"
    )

@app.route("/train", methods=["POST"])
@teacher_required
def train_trigger():
    try:
        proc = subprocess.run(["python", "train.py"], capture_output=True, text=True, timeout=300)
        out = proc.stdout + "\n---\n" + proc.stderr
        flash("Training finished successfully.", "success")
        return render_template("train_result.html", output=out)
    except Exception as e:
        flash(f"Training failed: {e}", "error")
        return redirect(url_for('dashboard'))

@app.route("/api/statistics")
@login_required
def get_statistics():
    conn = get_db_conn()
    user = conn.execute("SELECT role FROM users WHERE id=?", (session['user_id'],)).fetchone()
    
    if user['role'] == 'teacher':
        total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_attendance = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        recent_attendance = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE datetime(timestamp) >= datetime('now', '-7 days')"
        ).fetchone()[0]
    else:
        total_students = 1
        total_attendance = 0
        recent_attendance = 0
        student = conn.execute("SELECT id FROM students WHERE user_id=?", (session['user_id'],)).fetchone()
        if student:
            total_attendance = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE student_id=?",
                (student['id'],)
            ).fetchone()[0]
            recent_attendance = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE student_id=? AND datetime(timestamp) >= datetime('now', '-7 days')",
                (student['id'],)
            ).fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "total_students": total_students,
        "total_attendance": total_attendance,
        "recent_attendance": recent_attendance
    })# ===== Old Routes (kept for compatibility) =====
@app.route("/register_old", methods=["GET", "POST"])
def register_old():
    """Old student image registration (deprecated, use /register for user account)"""
    if request.method == "POST":
        sid = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        file = request.files.get("file")
        if not sid.isdigit() or name == "":
            flash("Student ID must be a number and name cannot be empty.", "error")
            return redirect(request.url)

        sid = int(sid)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[1].lower()
            existing = [f for f in os.listdir(UPLOAD_FOLDER) if f.startswith(f"{name}.{sid}.")]
            next_index = len(existing) + 1
            saved_name = f"{name}.{sid}.{next_index}.{ext}"
            saved_path = os.path.join(UPLOAD_FOLDER, saved_name)
            file.save(saved_path)
        else:
            flash("Please upload a JPG/PNG image of the face.", "error")
            return redirect(request.url)

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM students WHERE id=?", (sid,))
        if cur.fetchone() is None:
            import pickle
            placeholder = pickle.dumps(b"")
            cur.execute("INSERT INTO students (id, name, encoding) VALUES (?, ?, ?)", (sid, name, placeholder))
            conn.commit()
            flash(f"Inserted student {name} ({sid}) into DB.", "success")
        else:
            flash(f"Student ID {sid} already exists; added image to dataset.", "info")
        conn.close()
        return redirect(url_for("students"))
    return render_template("register.html")

def allowed_file(filename):
    """Check if file has allowed extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

if __name__ == "__main__":
    app.run(debug=True)
