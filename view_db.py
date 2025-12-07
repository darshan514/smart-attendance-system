import sqlite3

conn = sqlite3.connect('attendance.db')
c = conn.cursor()

print("=== STUDENTS ===")
for row in c.execute("SELECT * FROM students"):
    print(row)

print("\n=== ATTENDANCE ===")
for row in c.execute("SELECT * FROM attendance"):
    print(row)

conn.close()
