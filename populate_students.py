# populate_students.py
import sqlite3
import os
import pickle

DB = 'attendance.db'
dataset_dir = 'dataset'

if not os.path.exists(dataset_dir):
    print("dataset/ not found. Nothing to populate.")
    exit()

# build map id -> name from filenames like name.id.count.jpg
mapping = {}
for f in os.listdir(dataset_dir):
    parts = f.split('.')
    if len(parts) >= 3:
        name = parts[0]
        try:
            sid = int(parts[1])
        except:
            continue
        mapping[sid] = name

if not mapping:
    print("No valid dataset files found.")
    exit()

conn = sqlite3.connect(DB)
c = conn.cursor()

# For each id, insert if not exists. We'll store a small placeholder encoding (empty bytes pickled).
for sid, name in mapping.items():
    c.execute("SELECT id FROM students WHERE id=?", (sid,))
    if c.fetchone():
        print(f"Already in DB: {sid} -> {name}")
        continue
    placeholder = pickle.dumps(b'')  # placeholder encoding blob
    c.execute("INSERT INTO students (id, name, encoding) VALUES (?, ?, ?)", (sid, name, placeholder))
    print(f"Inserted: {sid} -> {name}")

conn.commit()
conn.close()
print("Done.")
