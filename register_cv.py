import cv2
import os
if not os.path.exists("dataset"):
    os.makedirs("dataset")

def register(student_id, student_name, samples=20):
    cam = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    count = 0
    print("Press SPACE to capture images. Close window or press ESC to stop early.")
    while True:
        ret, frame = cam.read()
        if not ret:
            print("No camera input")
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        for (x,y,w,h) in faces:
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
        cv2.imshow("Register - press SPACE", frame)
        key = cv2.waitKey(1)
        if key % 256 == 27:
            print("Cancelled by user")
            break
        elif key % 256 == 32:
            if len(faces) == 0:
                print("No face detected - try again")
                continue
            (x,y,w,h) = faces[0]
            face_img = gray[y:y+h, x:x+w]
            count += 1
            filename = f"dataset/{student_name}.{student_id}.{count}.jpg"
            cv2.imwrite(filename, face_img)
            print(f"Saved {filename} ({count}/{samples})")
            if count >= samples:
                print("Collected required samples.")
                break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    sid = input("Enter numeric student ID (e.g., 1): ").strip()
    name = input("Enter student name (no spaces recommended): ").strip()
    if not sid.isdigit() or name == "":
        print("Invalid input. ID must be a number and name non-empty.")
    else:
        register(int(sid), name, samples=20)