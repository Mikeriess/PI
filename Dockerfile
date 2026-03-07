# Use Python slim image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY app.py .

# Create directory for saved images
RUN mkdir -p /app/captured_images

# Set permissions
RUN chmod -R 777 /app/captured_images

# Expose the port Flask will run on
EXPOSE 8000

# Run the application
CMD ["python", "app.py"] 