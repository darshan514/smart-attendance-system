import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print("ret:", ret)
if ret:
    cv2.imshow("Camera Test", frame)
    cv2.waitKey(0)
cap.release()
cv2.destroyAllWindows()
