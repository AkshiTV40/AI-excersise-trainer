# Person Movement Tracker API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### Health Check
```
GET /health
```

Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "service": "person-tracker"
}
```

### Get Available Models
```
GET /api/models
```

Returns a list of available detection models.

**Response:**
```json
[
  {
    "name": "yolov8",
    "description": "YOLOv8 - Fast, accurate object detection with tracking support",
    "supports_tracking": true
  },
  {
    "name": "detr",
    "description": "DETR (DEtection TRansformer) - Transformer-based detection",
    "supports_tracking": false
  }
]
```

### Get Device Information
```
GET /api/device
```

Returns information about the device and available hardware acceleration.

**Response:**
```json
{
  "device": "cpu",
  "cuda_available": false,
  "mps_available": false,
  "cpu_count": 8,
  "cuda_device_count": null,
  "cuda_device_name": null
}
```

### Track Persons in Frame
```
POST /api/track
```

Process a single image frame for person detection and tracking.

**Request Body:**
```json
{
  "image": "base64_encoded_image_string",
  "session_id": "unique_session_id",
  "model_type": "yolov8",
  "enable_tracking": true
}
```

**Response:**
```json
{
  "success": true,
  "image": "base64_encoded_result_image",
  "detections": [
    {
      "bbox": [100, 100, 200, 200],
      "confidence": 0.95,
      "class_id": 0,
      "class_name": "person",
      "track_id": 1
    }
  ],
  "inference_time": 0.15,
  "track_count": 1,
  "model": "yolov8"
}
```

### Track from File Upload
```
POST /api/track/file
```

Upload an image file for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `file`: Image file
  - `model_type`: (optional) Model to use
  - `enable_tracking`: (optional) Enable tracking

**Response:** Same as `/api/track`

### Get Session Statistics
```
GET /api/session/{session_id}/stats
```

Returns statistics for a tracking session.

**Response:**
```json
{
  "session_id": "session_id",
  "frame_count": 100,
  "average_inference_time": 0.15,
  "total_tracks": 5
}
```

## WebSocket API

### Real-time Tracking
```
WS /ws/track
```

Connect to WebSocket for real-time tracking.

**Send Frame:**
```json
{
  "image": "base64_encoded_image_string"
}
```

**Receive Result:**
```json
{
  "success": true,
  "image": "base64_encoded_result_image",
  "detections": [...],
  "inference_time": 0.15,
  "track_count": 1,
  "model": "yolov8"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Invalid request data
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 100 requests per minute per IP
- WebSocket connections limited to 10 per IP

## Authentication

Currently, the API does not require authentication. For production use, implement:
- API key authentication
- JWT tokens
- OAuth 2.0