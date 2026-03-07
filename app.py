from flask import Flask, Response
import cv2
import threading
import time
from datetime import datetime
import os

app = Flask(__name__)

# Create images directory if it doesn't exist
IMAGES_DIR = 'captured_images'
os.makedirs(IMAGES_DIR, exist_ok=True)

# Global camera instance and lock
camera = None
# Global state to hold the latest jpeg frame
latest_frame = None
# Global variable to track the last time a frame was saved
last_save_time = 0
frame_lock = threading.Lock()

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        # Set resolution to 1080p
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        # Wait a bit longer for the camera to adjust its focus/exposure
        time.sleep(2)
        
        actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = camera.get(cv2.CAP_PROP_FPS)
        print(f"Camera initialized with resolution: {actual_width}x{actual_height} @ {actual_fps}fps")
    return camera

def capture_camera_loop():
    global latest_frame, last_save_time
    # Initialize the camera
    cam = get_camera()
    
    while True:
        success, frame = cam.read()
        if not success:
            time.sleep(0.1)
            continue
        
        # Periodically save the frame to disk every 60 seconds
        current_time = time.time()
        if current_time - last_save_time >= 60:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(IMAGES_DIR, f'frame_{timestamp}.jpg')
            cv2.imwrite(filename, frame)
            last_save_time = current_time

        # Encode frame to JPEG with slightly reduced quality for better performance on Pi
        # You can adjust the quality value (0-100), 80 is a good balance between size and quality.
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        
        if ret:
            with frame_lock:
                latest_frame = buffer.tobytes()
        
        # A small sleep to prevent 100% CPU usage on the Pi
        time.sleep(0.01)

def generate_frames():
    while True:
        with frame_lock:
            frame_to_yield = latest_frame
            
        if frame_to_yield is not None:
             # Yield the frame in byte format
             yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_to_yield + b'\r\n')
        
        # Determine the refresh rate of the stream.
        # ~30fps -> 0.03s
        time.sleep(0.03)

# Start the dedicated camera capture thread
capture_thread = threading.Thread(target=capture_camera_loop, daemon=True)
capture_thread.start()

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Raspberry Pi Camera Stream</title>
            <style>
                body { margin: 0; background: black; }
                img { width: 100%; height: 100vh; object-fit: contain; }
            </style>
        </head>
        <body>
            <img src="/video_feed">
        </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8000, threaded=True)
    finally:
        # Cleanup camera on shutdown
        if camera is not None:
            camera.release() 