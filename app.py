import cv2
import gradio as gr

def video_feed():
    # Initialize the webcam (0 is usually the default USB webcam)
    cap = cv2.VideoCapture(0)
    
    # Ensure the webcam is opened correctly
    if not cap.isOpened():
        raise RuntimeError("Failed to open webcam")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert BGR (OpenCV format) to RGB (what Gradio expects)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            yield frame
    
    finally:
        # Release the webcam when done
        cap.release()

# Create Gradio interface
def create_ui():
    return gr.Interface(
        fn=video_feed,
        inputs=None,
        outputs="image",
        live=True,
        title="Raspberry Pi Webcam Stream",
        description="Live video stream from USB webcam"
    )

if __name__ == "__main__":
    ui = create_ui()
    # Launch the interface on 0.0.0.0 to make it accessible from other devices
    ui.launch(server_name="0.0.0.0", server_port=7860) 