FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download models
RUN python -c "from transformers import AutoModelForObjectDetection, AutoImageProcessor; from ultralytics import YOLO; YOLO('yolov8n.pt'); AutoImageProcessor.from_pretrained('facebook/detr-resnet-50', cache_dir='./models'); AutoModelForObjectDetection.from_pretrained('facebook/detr-resnet-50', cache_dir='./models')"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]