import cv2
import sqlite3
from datetime import datetime
import os
import numpy as np

DB = 'attendance.db'

def mark_attendance(student_id, name):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO attendance (student_id, name, timestamp) VALUES (?, ?, ?)",
              (student_id, name, timestamp))
    conn.commit()
    conn.close()
    print(f"Marked {name} at {timestamp}")

def load_id_name_map():
    mapping = {}
    if not os.path.exists('dataset'):
        return mapping
    for f in os.listdir('dataset'):
        parts = f.split(".")
        if len(parts) >= 3:
            name = parts[0]
            sid = int(parts[1])
            mapping[sid] = name
    return mapping

if not os.path.exists('trainer/trainer.yml'):
    print("Model not found. Run train.py first.")
    exit()

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
id_name = load_id_name_map()
recognized_set = set()

cam = cv2.VideoCapture(0)
print("Running recognizer. Press 'q' to quit.")

while True:
    ret, frame = cam.read()
    if not ret:
        print("No camera input")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    for (x, y, w, h) in faces:
        roi = gray[y:y+h, x:x+w]
        sid, confidence = recognizer.predict(roi)

        if confidence < 80:
            name = id_name.get(sid, f"ID{sid}")
            if sid not in recognized_set:
                mark_attendance(sid, name)
                recognized_set.add(sid)
            label = f"{name} ({int(confidence)})"
        else:
            label = "Unknown"

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("Attendance - press q to quit", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
