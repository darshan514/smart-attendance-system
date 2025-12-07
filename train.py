import cv2
import numpy as np
from os import listdir
from os.path import isfile, join
import os

dataset_path = "dataset"
if not os.path.exists(dataset_path):
    print("dataset/ not found. Run register_cv.py to collect images first.")
    exit()

images = [f for f in listdir(dataset_path) if isfile(join(dataset_path, f))]

face_samples = []
ids = []

face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

for imagePath in images:
    try:
        img = cv2.imread(join(dataset_path, imagePath), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        parts = imagePath.split(".")
        if len(parts) < 3:
            continue
        student_id = int(parts[1])
        faces = face_detector.detectMultiScale(img)
        for (x, y, w, h) in faces:
            face_samples.append(img[y:y+h, x:x+w])
            ids.append(student_id)
    except Exception as e:
        print("Skipped", imagePath, "error:", e)

if len(ids) == 0:
    print("No training data found in dataset/ — run register_cv.py first.")
    exit()

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(face_samples, np.array(ids))

if not os.path.exists('trainer'):
    os.makedirs('trainer')
recognizer.write('trainer/trainer.yml')

print(f"Training completed. {len(np.unique(ids))} unique IDs. Model saved to trainer/trainer.yml")
