# Plan: Distributed Webcam Streaming (Pi -> TOASTER)

**Goal:** Reduce the workload on the Raspberry Pi while allowing multiple users on the home network to view a webcam stream. The entire stack should be built with Python and Docker Compose for easy debugging.

## Architecture Overview

We will split the current `app.py` into two separate microservices:

1.  **The Pi Producer (Runs on Raspberry Pi):**
    *   **Role:** Capture video from `/dev/video0` and broadcast the raw or lightly compressed frames over the local network.
    *   **Technology:** Python, OpenCV, and **ZeroMQ** (PyZMQ) or a simple UDP socket. ZeroMQ is highly recommended for Python-to-Python streaming because it handles network buffering, dropped connections, and message framing automatically without adding complexity.
    *   **Implementation:** A minimal Python script that reads from the camera, encodes the frame as JPEG, and publishes it to a specific port using a ZeroMQ `PUB` (Publisher) socket. It will *not* host a web server.
    *   **Docker:** A `docker-compose.yml` that only mounts the camera and exposes the ZeroMQ port.

2.  **The TOASTER Server (Runs on the 64GB/22-core machine):**
    *   **Role:** Receive the frames from the Pi, save snapshots periodically, and host the Flask web interface for end users.
    *   **Technology:** Python, OpenCV (for saving), Flask, and ZeroMQ.
    *   **Implementation:** A Python script that uses a ZeroMQ `SUB` (Subscriber) socket to connect to the Pi's IP address. It will maintain a global `latest_frame` buffer (like our recent optimization) to serve the Flask app. It will also handle saving the images to disk every 60 seconds.
    *   **Docker:** A `docker-compose.yml` that exposes port 8000 for the web interface and maps a volume for saved images.

## Structure

### Restructuring the Repository
We will split the repository into two directories: `pi_node` and `toaster_node`.

#### pi_node/docker-compose.yml
A simple compose file mapping `/dev/video0` and exposing port `5555`.

#### pi_node/Dockerfile
Builds the Python environment for the Pi.

#### pi_node/requirements.txt
Needs `opencv-python`, `numpy`, and `pyzmq`. (No Flask).

#### pi_node/streamer.py
Reads from OpenCV and uses a ZeroMQ publisher to broadcast JPEG bytes.

#### toaster_node/docker-compose.yml
Exposes port `8000` for the web UI and maps a volume for `captured_images`.

#### toaster_node/Dockerfile
Builds the Python environment for the Toaster.

#### toaster_node/requirements.txt
Needs `flask`, `opencv-python`, `numpy`, and `pyzmq`.

#### toaster_node/server.py
Uses a ZeroMQ subscriber to receive frames from the Pi. Runs the Flask app (serving `latest_frame`) and handles the 60-second snapshot saving.

#### Files to be replaced/deleted from the old setup
*   `app.py`
*   `docker-compose.yml`
*   `Dockerfile`
*   `requirements.txt`
(These will be moved/deleted in favor of the new folder structure).
