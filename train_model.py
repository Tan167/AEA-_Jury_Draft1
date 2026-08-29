"""
Step 2: Train the LBPH face recognizer on the captured dataset.
This produces model.yml + labels.json, used by BOTH the cloud server
(Standard IoT path) and the edge client (Edge Analytics path) — the
recognition logic itself is identical in both architectures, only
*where* it runs differs.

Usage:
    python train_model.py
"""
import json
import os
import cv2
import numpy as np

DATASET_DIR = "dataset"
MODEL_PATH = "model.yml"
LABELS_PATH = "labels.json"


def train():
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    faces = []
    labels = []
    label_map = {}  # id -> name

    for idx, name in enumerate(sorted(os.listdir(DATASET_DIR))):
        person_dir = os.path.join(DATASET_DIR, name)
        if not os.path.isdir(person_dir):
            continue
        label_map[idx] = name
        for fname in os.listdir(person_dir):
            img_path = os.path.join(person_dir, fname)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            faces.append(img)
            labels.append(idx)

    if not faces:
        raise RuntimeError("No training images found. Run capture_faces.py first.")

    recognizer.train(faces, np.array(labels))
    recognizer.save(MODEL_PATH)

    with open(LABELS_PATH, "w") as f:
        json.dump(label_map, f)

    print(f"Trained on {len(faces)} images across {len(label_map)} student(s).")
    print(f"Saved {MODEL_PATH} and {LABELS_PATH}")


if __name__ == "__main__":
    train()
