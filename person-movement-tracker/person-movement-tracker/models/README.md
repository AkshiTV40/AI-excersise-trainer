# Models Directory

This directory contains downloaded AI models for the Person Movement Tracker.

## Models

### YOLOv8
- **File**: `yolov8n.pt`
- **Description**: Fast and accurate object detection
- **Size**: ~6MB
- **Speed**: Very Fast
- **Use Case**: Real-time tracking

### DETR (DEtection TRansformer)
- **Model**: `facebook/detr-resnet-50`
- **Description**: Transformer-based object detection
- **Size**: ~150MB
- **Speed**: Medium
- **Use Case**: High accuracy detection

### YOLOS
- **Model**: `hustvl/yolos-small`
- **Description**: Vision Transformer for object detection
- **Size**: ~200MB
- **Speed**: Medium
- **Use Case**: Alternative to DETR

## Downloading Models

Models are automatically downloaded when:
1. Running `scripts/setup.sh`
2. Running `scripts/download_models.py`
3. First time using a model

## Manual Download

```bash
python scripts/download_models.py
```

## Model Cache

HuggingFace models are cached in this directory. To clear cache:

```bash
rm -rf models/*
python scripts/download_models.py
```

## Custom Models

To use custom models:
1. Place model files in this directory
2. Update `backend/src/models/detector_factory.py` to register the model
3. Restart the backend server