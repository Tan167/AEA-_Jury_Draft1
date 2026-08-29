"""
Step 1: Capture training photos of the one student.
Run this once on laptop (webcam) now, and again on Tuesday with the
Pi camera if you want fresher training data (not required — the model
trained on laptop photos will still work fine on the Pi).

Usage:
    python capture_faces.py --name tanay --count 25
"""
import argparse
import os
import cv2

FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def capture(name: str, count: int, camera_index: int = 0):
    out_dir = os.path.join("dataset", name)
    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera. Check camera_index.")

    saved = 0
    print(f"Capturing {count} face images for '{name}'. Look at the camera.")
    while saved < count:
        ok, frame = cap.read()
        if not ok:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        for (x, y, w, h) in faces:
            face_img = gray[y:y + h, x:x + w]
            face_img = cv2.resize(face_img, (200, 200))
            path = os.path.join(out_dir, f"{saved:03d}.jpg")
            cv2.imwrite(path, face_img)
            saved += 1
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            break  # one face per frame is enough

        cv2.putText(frame, f"Captured: {saved}/{count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Capture - press q to stop early", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. Saved {saved} images to {out_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Student name/id")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--camera-index", type=int, default=0)
    args = parser.parse_args()
    capture(args.name, args.count, args.camera_index)
