# PS20 — Standard IoT vs Edge Analytics (Attendance System)

## Setup (once)
```bash
pip install -r requirements.txt
```

## Sunday run order (laptop webcam)

1. **Capture training photos of the one student:**
   ```bash
   python capture_faces.py --name tanay --count 25
   ```

2. **Train the recognizer:**
   ```bash
   python train_model.py
   ```

3. **Start the cloud server** (leave running in its own terminal):
   ```bash
   python cloud_server.py
   ```

4. **Run the Standard IoT path** (new terminal):
   ```bash
   python standard_iot_client.py --captures 10
   python standard_iot_client.py --captures 5 --outage   # simulate no internet
   ```

5. **Run the Edge Analytics path** (new terminal):
   ```bash
   python edge_client.py --captures 10
   python edge_client.py --captures 5 --outage   # simulate no internet
   ```

6. **View the comparison:**
   ```bash
   streamlit run dashboard.py
   ```

## Tuesday (real hardware)

Only one thing changes: the camera source.
- If using the Pi's inbuilt camera module (not a USB webcam), replace
  `cv2.VideoCapture(camera_index)` in `capture_faces.py`,
  `standard_iot_client.py`, and `edge_client.py` with a `picamera2`
  capture, OR just plug in a USB webcam and keep `camera_index=0` —
  the simplest option if you want zero code changes.
- Copy this whole folder to the Pi, `pip install -r requirements.txt`
  there (opencv-contrib-python installs quickly via pip — no compiling).
- Re-run steps 3–6 on the Pi to get real-hardware numbers for the report.
- Keep your Sunday laptop numbers too — a "simulated vs. real hardware"
  comparison is a nice bonus point in the results section.

## What each metric proves
- **Latency**: Standard IoT pays a network round trip for every single
  frame; Edge Analytics only pays it for the occasional summary.
- **Bandwidth**: raw JPEG frames (tens of KB) vs. a tiny JSON record
  (~40 bytes) — this is the clearest number in your whole report.
- **Reliability**: kill the connection (`--outage`) and Standard IoT
  loses attendance records; Edge Analytics keeps working and queues
  the sync for later.
- **Privacy**: Standard IoT transmits raw face images over the network;
  Edge Analytics never sends the image anywhere, only the decision.
