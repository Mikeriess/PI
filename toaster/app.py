from flask import Flask, Response, render_template, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)

PI_STREAM_URL = os.environ.get("PI_STREAM_URL", "http://192.168.1.XX:8000/video_feed")

latest_frame = None
frame_lock = threading.Lock()
relay_connected = False

def relay_loop():
    global latest_frame, relay_connected
    while True:
        try:
            print(f"Connecting to Pi stream: {PI_STREAM_URL}")
            r = requests.get(PI_STREAM_URL, stream=True, timeout=10)
            relay_connected = True
            print("Relay connected.")
            buf = b""
            for chunk in r.iter_content(chunk_size=4096):
                buf += chunk
                # Find complete JPEG frame using SOI/EOI markers
                soi = buf.find(b'\xff\xd8')
                eoi = buf.find(b'\xff\xd9')
                if soi != -1 and eoi != -1 and eoi > soi:
                    jpeg = buf[soi:eoi + 2]
                    with frame_lock:
                        latest_frame = jpeg
                    buf = buf[eoi + 2:]
                # Flush buffer if it grows too large (corrupted stream)
                if len(buf) > 500_000:
                    buf = b""
        except Exception as e:
            relay_connected = False
            print(f"Relay error: {e} — reconnecting in 3s")
            time.sleep(3)

def generate_frames():
    while True:
        with frame_lock:
            frame_to_yield = latest_frame
        if frame_to_yield is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_to_yield + b'\r\n')
        time.sleep(0.03)

relay_thread = threading.Thread(target=relay_loop, daemon=True)
relay_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    return jsonify({"status": "ok", "relay_connected": relay_connected})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
