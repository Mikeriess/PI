from flask import Flask, Response, jsonify
import cv2
import threading
import time

app = Flask(__name__)

camera = None
latest_frame = None
frame_lock = threading.Lock()

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        time.sleep(2)
        actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = camera.get(cv2.CAP_PROP_FPS)
        print(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
    return camera

def capture_camera_loop():
    global latest_frame
    cam = get_camera()
    while True:
        success, frame = cam.read()
        if not success:
            time.sleep(0.1)
            continue
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            with frame_lock:
                latest_frame = buffer.tobytes()
        time.sleep(0.01)

def generate_frames():
    while True:
        with frame_lock:
            frame_to_yield = latest_frame
        if frame_to_yield is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_to_yield + b'\r\n')
        time.sleep(0.03)

capture_thread = threading.Thread(target=capture_camera_loop, daemon=True)
capture_thread.start()

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8000, threaded=True)
    finally:
        if camera is not None:
            camera.release()
