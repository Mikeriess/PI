# Raspberry Pi Webcam Livestream

A Docker-containerized application that streams webcam feed to a local website using OpenCV and Gradio.

## Features

- Live webcam streaming through a web interface
- Containerized solution using Docker
- Built with OpenCV and Gradio
- Easy to deploy on Raspberry Pi
- Accessible from any device on the local network

## Prerequisites

- Raspberry Pi with Raspberry Pi OS
- Docker installed
- USB webcam connected to Raspberry Pi
- SSH access to Raspberry Pi

## Installation

1. Clone this repository or copy the files to your Raspberry Pi:
   ```bash
   git clone <repository-url>
   cd webcam-stream
   ```

2. Build the Docker image:
   ```bash
   docker build -t webcam-stream .
   ```

3. Run the container:
   ```bash
   docker run --device=/dev/video0:/dev/video0 -p 7860:7860 webcam-stream
   ```

## Usage

1. After starting the container, open a web browser
2. Navigate to: `http://<raspberry-pi-ip>:7860`
3. The webcam stream should appear automatically in the browser
