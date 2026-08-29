"""
Edge Analytics path: the device is 'smart'. It captures a frame and
recognizes the face LOCALLY (same recognize.py logic the cloud server
uses) — the raw image never leaves the device. Only a tiny JSON
attendance record gets sent to the cloud for the dashboard.

Also demonstrates reliability during an outage: if the cloud is
unreachable, the record is queued locally instead of being lost, and
attendance was already decided locally either way — that's the point.

Run cloud_server.py first, then this in a separate terminal.

Usage:
    python edge_client.py
    python edge_client.py --outage
"""
import argparse
import csv
import json
import os
import time

import cv2
import requests

from recognize import load_recognizer, recognize_frame

METRICS_CSV = "metrics_edge.csv"
QUEUE_FILE = "edge_offline_queue.jsonl"
FIELDS = ["timestamp", "latency_ms", "bytes_sent", "status", "outage_simulated"]
CLOUD_URL = "http://127.0.0.1:5000/attendance"


def log_metric(latency_ms, bytes_sent, status, outage):
    new_file = not os.path.exists(METRICS_CSV)
    with open(METRICS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "latency_ms": round(latency_ms, 1),
            "bytes_sent": bytes_sent,
            "status": status,
            "outage_simulated": outage,
        })


def run(camera_index: int, captures: int, outage: bool):
    recognizer, label_map = load_recognizer()
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    url = "http://127.0.0.1:9999/attendance" if outage else CLOUD_URL

    for i in range(captures):
        ok, frame = cap.read()
        if not ok:
            continue

        # Recognition happens HERE, on-device — no image ever sent out.
        recog_start = time.time()
        result = recognize_frame(frame, recognizer, label_map)
        local_processing_ms = (time.time() - recog_start) * 1000

        record = {
            "name": result["name"],
            "status": "present" if result["status"] == "present" else "absent",
        }
        payload = json.dumps(record).encode()

        start = time.time()
        try:
            requests.post(url, json=record, timeout=2)
            latency_ms = (time.time() - start) * 1000
            status = "synced"
            print(f"[{i+1}/{captures}] {record} local_ms={local_processing_ms:.1f} "
                  f"sync_latency={latency_ms:.1f}ms bytes_sent={len(payload)}")
        except requests.exceptions.RequestException:
            latency_ms = (time.time() - start) * 1000
            status = "queued_offline"
            with open(QUEUE_FILE, "a") as f:
                f.write(json.dumps(record) + "\n")
            print(f"[{i+1}/{captures}] {record} — cloud unreachable, "
                  f"queued locally (attendance still recorded on-device)")

        log_metric(latency_ms, len(payload), status, outage)
        time.sleep(1)

    cap.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--captures", type=int, default=10)
    parser.add_argument("--outage", action="store_true",
                         help="Point at an unreachable port to simulate no internet")
    args = parser.parse_args()
    run(args.camera_index, args.captures, args.outage)
