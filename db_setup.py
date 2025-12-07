import sqlite3

conn = sqlite3.connect('attendance.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    encoding BLOB NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    name TEXT,
    timestamp TEXT
)
''')

conn.commit()
conn.close()
print("Database created / verified: attendance.db")
