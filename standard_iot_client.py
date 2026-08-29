"""
Standard IoT path: the device is 'dumb'. It just captures a frame and
ships the raw image to the cloud, which does all the recognition work.

Run cloud_server.py first, then this in a separate terminal.

Usage:
    python standard_iot_client.py                 # normal run, 10 captures
    python standard_iot_client.py --outage         # simulate no internet
    python standard_iot_client.py --camera-index 0
"""
import argparse
import csv
import os
import time

import cv2
import requests

METRICS_CSV = "metrics_standard.csv"
FIELDS = ["timestamp", "latency_ms", "bytes_sent", "status", "outage_simulated"]
CLOUD_URL = "http://127.0.0.1:5000/recognize"


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
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    url = "http://127.0.0.1:9999/recognize" if outage else CLOUD_URL  # bad port = simulated outage

    for i in range(captures):
        ok, frame = cap.read()
        if not ok:
            continue

        _, encoded = cv2.imencode(".jpg", frame)
        payload = encoded.tobytes()

        start = time.time()
        try:
            resp = requests.post(url, data=payload,
                                  headers={"Content-Type": "image/jpeg"}, timeout=2)
            latency_ms = (time.time() - start) * 1000
            result = resp.json()
            status = result.get("status", "error")
            print(f"[{i+1}/{captures}] status={status} latency={latency_ms:.1f}ms "
                  f"bytes_sent={len(payload)}")
        except requests.exceptions.RequestException:
            latency_ms = (time.time() - start) * 1000
            status = "failed_no_connection"
            print(f"[{i+1}/{captures}] FAILED (simulated outage) after {latency_ms:.1f}ms")

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
