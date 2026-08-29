"""
The 'cloud' in both architectures.

- Standard IoT path (edge device is 'dumb'): device sends the RAW IMAGE
  here via /recognize. This server does the face recognition and sends
  the result back. Heavy payload, does all the work.

- Edge Analytics path (edge device is 'smart'): device already did
  recognition locally and just sends a tiny attendance RECORD here via
  /attendance for storage/dashboard purposes. Tiny payload, no work
  done here.

Run this first, then run standard_iot_client.py / edge_client.py in
separate terminals.

Usage:
    python cloud_server.py
"""
import csv
import os
import time

import cv2
import numpy as np
from flask import Flask, request, jsonify

from recognize import load_recognizer, recognize_frame

app = Flask(__name__)
recognizer, label_map = load_recognizer()

ATTENDANCE_CSV = "attendance.csv"
FIELDS = ["timestamp", "name", "status", "source"]


def log_attendance(name, status, source):
    new_file = not os.path.exists(ATTENDANCE_CSV)
    with open(ATTENDANCE_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "name": name,
            "status": status,
            "source": source,  # "standard_iot" or "edge_analytics"
        })


@app.route("/recognize", methods=["POST"])
def recognize():
    """Standard IoT path: receives a raw JPEG frame, does ALL processing here."""
    # Simulate real network/processing delay a cloud round trip would have
    time.sleep(0.15)

    img_bytes = request.data
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    result = recognize_frame(frame, recognizer, label_map)
    if result["status"] == "present":
        log_attendance(result["name"], "present", "standard_iot")

    result["bytes_received"] = len(img_bytes)
    return jsonify(result)


@app.route("/attendance", methods=["POST"])
def attendance():
    """Edge Analytics path: receives an already-decided tiny record, just stores it."""
    data = request.get_json()
    log_attendance(data.get("name"), data.get("status"), "edge_analytics")
    return jsonify({"stored": True, "bytes_received": len(request.data)})


if __name__ == "__main__":
    app.run(port=5000, debug=False)
