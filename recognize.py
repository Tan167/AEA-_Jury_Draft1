"""
Shared recognition logic. Both the Standard IoT path (cloud_server.py)
and the Edge Analytics path (edge_client.py) call this — the only
difference between the two architectures is WHERE this function runs
and WHAT gets sent over the network before/after it.
"""
import json
import cv2

MODEL_PATH = "model.yml"
LABELS_PATH = "labels.json"
CONFIDENCE_THRESHOLD = 70  # LBPH: lower distance = better match

FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def load_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)
    with open(LABELS_PATH) as f:
        label_map = {int(k): v for k, v in json.load(f).items()}
    return recognizer, label_map


def recognize_frame(frame_bgr, recognizer, label_map):
    """
    Takes a BGR image (as read by cv2), returns:
        {"status": "present"|"absent", "name": str|None, "confidence": float|None}
    """
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        return {"status": "absent", "name": None, "confidence": None}

    x, y, w, h = faces[0]
    face_img = cv2.resize(gray[y:y + h, x:x + w], (200, 200))
    label_id, distance = recognizer.predict(face_img)

    if distance <= CONFIDENCE_THRESHOLD:
        return {"status": "present", "name": label_map.get(label_id), "confidence": float(distance)}
    return {"status": "unrecognized", "name": None, "confidence": float(distance)}
