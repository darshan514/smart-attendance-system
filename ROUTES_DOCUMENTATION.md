# Smart Attendance System - Complete Route Documentation

## All Available Routes (17 Routes)

### Authentication Routes

#### `/` (GET)
**Purpose**: Home page redirect
- If logged in: Redirects to `/dashboard`
- If not logged in: Redirects to `/login`

#### `/login` (GET, POST)
**Purpose**: User authentication
- **GET**: Display login form with role selector
- **POST**: Process login (email + password + role)
- **Auth Required**: No
- **Template**: `templates/login.html`
- **Redirect**: `/dashboard` on success

#### `/register` (GET, POST)
**Purpose**: New user account creation
- **GET**: Display registration form
- **POST**: Create new user account
- **Auth Required**: No
- **Template**: `templates/register.html`
- **Features**:
  - Role selection (teacher/student)
  - Password validation (min 6 characters)
  - Email uniqueness check
  - Password hashing with Werkzeug
- **Redirect**: `/login` on success

#### `/logout` (GET)
**Purpose**: Clear user session and logout
- **Auth Required**: Yes
- **Action**: Clears all session data
- **Redirect**: `/login`
- **Message**: "You have been logged out."

---

### Dashboard Routes

#### `/dashboard` (GET)
**Purpose**: Role-based main dashboard
- **Auth Required**: Yes (all users)
- **Teacher View**: Statistics, quick actions, recent activity
  - Template: `templates/teacher_dashboard.html`
  - Passes: user, students_count, attendance_count, trainer_exists
  - Shows: Stats cards, quick actions, system info, recent activity
- **Student View**: Personal attendance, statistics
  - Template: `templates/student_dashboard.html`
  - Passes: user, student, attendance_count, recent_attendance
  - Shows: Personal stats, attendance history, quick info

---

### Profile Routes

#### `/profile` (GET)
**Purpose**: View user profile
- **Auth Required**: Yes
- **Template**: `templates/profile.html`
- **Passes**: user, student (if student user)
- **Displays**:
  - Full name
  - Email address
  - Phone number
  - User role
  - Account creation date
  - Security information

#### `/profile/edit` (GET, POST)
**Purpose**: Edit user profile
- **Auth Required**: Yes
- **GET**: Display edit form
- **POST**: Update profile in database
- **Template**: `templates/edit_profile.html`
- **Passes**: user
- **Editable Fields**: full_name, phone
- **Non-Editable**: email, role
- **Redirect**: `/profile` on success

#### `/change-password` (GET, POST)
**Purpose**: Change account password
- **Auth Required**: Yes
- **GET**: Display password change form
- **POST**: Update password
- **Template**: `templates/change_password.html`
- **Validations**:
  - Current password must be correct
  - New password min 6 characters
  - New passwords must match
- **Redirect**: `/profile` on success

---

### Teacher-Only Routes

#### `/students` (GET)
**Purpose**: View and manage student list
- **Auth Required**: Yes
- **Role Required**: teacher
- **Template**: `templates/students.html`
- **Features**:
  - Display all students
  - Search by name or ID
  - Pagination support
  - Delete options
  - View individual student details
- **Query Parameters**: `?search=<term>`
- **Database Query**: SELECT students by name/ID

#### `/attendance` (GET)
**Purpose**: View attendance records
- **Auth Required**: Yes
- **Role Required**: teacher
- **Template**: `templates/attendance.html`
- **Features**:
  - Display all attendance records
  - Sorted by most recent first
  - Search by student name or ID
  - Timestamps for each record
- **Query Parameters**: `?search=<term>`
- **Database Query**: SELECT attendance records

#### `/student/<int:student_id>` (GET)
**Purpose**: View individual student details
- **Auth Required**: Yes
- **Role Required**: teacher
- **URL Parameters**: student_id (integer)
- **Template**: `templates/student_detail.html`
- **Displays**:
  - Student information (ID, name, email, phone)
  - Attendance history (last 10 records)
  - Total attendance count
  - Action buttons (edit, delete)
- **Error Handling**: 404 if student not found

#### `/delete_student/<int:student_id>` (POST)
**Purpose**: Delete student and attendance records
- **Auth Required**: Yes
- **Role Required**: teacher
- **URL Parameters**: student_id (integer)
- **Actions**:
  1. Delete all attendance records for student
  2. Delete student from database
  3. Delete student images from dataset folder
- **Redirect**: `/students`
- **Message**: "Student [name] and all their records deleted."

#### `/export_csv` (GET)
**Purpose**: Export attendance as CSV file
- **Auth Required**: Yes
- **Role Required**: teacher
- **Returns**: CSV file download
- **Columns**: student_id, name, timestamp
- **Filename**: attendance_export.csv
- **Format**: Excel-compatible

#### `/train` (POST)
**Purpose**: Trigger face recognition model training
- **Auth Required**: Yes
- **Role Required**: teacher
- **Action**: Runs `train.py` subprocess
- **Timeout**: 300 seconds
- **Template**: `templates/train_result.html`
- **Returns**: Training output (stdout + stderr)
- **Error Handling**: Captures and displays errors

---

### API Routes

#### `/api/statistics` (GET)
**Purpose**: Get JSON statistics for dashboards
- **Auth Required**: Yes
- **Content-Type**: application/json
- **Returns**:
  ```json
  {
    "total_students": integer,
    "total_attendance": integer,
    "recent_attendance": integer,
    "top_students": [
      {"student_id": int, "name": str, "count": int},
      ...
    ]
  }
  ```
- **Role-Aware**:
  - Teacher: All statistics
  - Student: Only their own statistics
- **Recent Attendance**: Last 7 days

---

### Helper Routes (Deprecated/Compatibility)

#### `/register_old` (GET, POST)
**Purpose**: Old student image registration (deprecated)
- **Kept for**: Backward compatibility
- **Use**: For uploading face images to dataset
- **Replaced by**: New user registration system
- **Method**: Form-based image upload

---

## Route Summary Table

| Route | Method | Auth | Role | Purpose |
|-------|--------|------|------|---------|
| `/` | GET | No | - | Home redirect |
| `/login` | GET/POST | No | - | Login |
| `/register` | GET/POST | No | - | Register |
| `/logout` | GET | Yes | Any | Logout |
| `/dashboard` | GET | Yes | Any | Main dashboard |
| `/profile` | GET | Yes | Any | View profile |
| `/profile/edit` | GET/POST | Yes | Any | Edit profile |
| `/change-password` | GET/POST | Yes | Any | Change password |
| `/students` | GET | Yes | Teacher | Student list |
| `/attendance` | GET | Yes | Teacher | Attendance records |
| `/student/<id>` | GET | Yes | Teacher | Student details |
| `/delete_student/<id>` | POST | Yes | Teacher | Delete student |
| `/export_csv` | GET | Yes | Teacher | Export CSV |
| `/train` | POST | Yes | Teacher | Train model |
| `/api/statistics` | GET | Yes | Any | Get statistics |

---

## Request/Response Examples

### Example: Login Request
```
POST /login
Content-Type: application/x-www-form-urlencoded

email=teacher@example.com&password=securepass&role=teacher
```

### Example: Statistics Response
```
GET /api/statistics

{
  "total_students": 45,
  "total_attendance": 1250,
  "recent_attendance": 180,
  "top_students": [
    {"student_id": 1, "name": "John Doe", "count": 42},
    {"student_id": 2, "name": "Jane Smith", "count": 38}
  ]
}
```

### Example: Register Request
```
POST /register
Content-Type: application/x-www-form-urlencoded

full_name=Test User
&email=test@example.com
&password=test123456
&confirm_password=test123456
&role=teacher
&phone=555-0000
```

---

## Error Handling

### Common HTTP Status Codes

- **200 OK**: Request successful
- **302 Found**: Redirect (login required)
- **400 Bad Request**: Invalid form data
- **404 Not Found**: Student not found
- **500 Internal Server Error**: Server error

### Flash Messages

```python
# Success message
flash("Profile updated successfully!", "success")

# Error message
flash("Invalid email or password.", "error")

# Info message
flash("Student ID already exists.", "info")
```

---

## Decorator System

### @login_required
```python
@login_required
def some_route():
    # Only executed if user is logged in
    # Redirects to login if not authenticated
```

### @teacher_required
```python
@teacher_required
def teacher_only_route():
    # Only teachers can access
    # Students get error message and redirect
```

---

## Session Variables

After login, session contains:
```python
session['user_id']      # User ID in database
session['email']        # User email
session['role']         # 'teacher' or 'student'
session['full_name']    # User's full name
```

---

## Form Processing

### Login Form
- Fields: email, password, role
- Validation: Both fields required
- Processing: Password hashed check

### Register Form
- Fields: email, password, confirm_password, full_name, role, phone
- Validation: 
  - Passwords match
  - Min 6 characters
  - Email not duplicate
- Processing: Password hashed

### Edit Profile Form
- Fields: full_name, phone
- Validation: Full name required
- Processing: Direct database update

### Change Password Form
- Fields: current_password, new_password, confirm_password
- Validation:
  - Current password verified
  - New passwords match
  - Min 6 characters
- Processing: New password hashed

---

## URL Query Parameters

### Search
```
/students?search=john
/attendance?search=12345
```

### Pagination (future enhancement)
```
/students?page=2&per_page=10
```

---

## MIME Types Returned

| Route | MIME Type |
|-------|-----------|
| `/login` | text/html |
| `/students` | text/html |
| `/api/statistics` | application/json |
| `/export_csv` | text/csv |

---

## Authentication Flow

```
1. User visits app → Redirected to /login
2. User registers → Creates account → Redirected to /login
3. User logs in → Session created → Redirected to /dashboard
4. User accesses protected route → Session checked → Route executed
5. User logs out → Session cleared → Redirected to /login
```

---

## Database Queries per Route

### /students
```sql
SELECT id, name, email, phone FROM students 
WHERE LOWER(name) LIKE ? OR LOWER(email) LIKE ?
ORDER BY id
```

### /attendance
```sql
SELECT id, student_id, name, timestamp FROM attendance
WHERE LOWER(name) LIKE ? OR CAST(student_id AS TEXT) LIKE ?
ORDER BY timestamp DESC
```

### /api/statistics (Teacher)
```sql
SELECT COUNT(*) FROM students
SELECT COUNT(*) FROM attendance
SELECT COUNT(*) FROM attendance 
  WHERE datetime(timestamp) >= datetime('now', '-7 days')
SELECT student_id, name, COUNT(*) FROM attendance
  GROUP BY student_id ORDER BY COUNT(*) DESC LIMIT 5
```

---

## Performance Considerations

- **Search Operations**: Uses LIKE with LOWER() for case-insensitive search
- **Pagination**: Ready for implementation (not yet active)
- **API Caching**: Statistics calculated on each request
- **File Operations**: Images stored in /dataset folder
- **Database Indexing**: Primary keys on id, foreign keys on user_id/student_id

---

## Security Implementations

- **SQL Injection**: All queries use parameterized statements
- **Password Storage**: Werkzeug hashing with salt
- **Session Management**: Flask secure session
- **CSRF**: Flask built-in protection
- **Input Validation**: Form data validated before processing
- **Email Uniqueness**: Enforced at database level

---

**Last Updated**: December 7, 2025
**Total Routes**: 17
**Status**: ✅ All Routes Functional
