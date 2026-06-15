# Person Movement Tracker

A real-time person detection and tracking system powered by AI. Built with FastAPI, React, and state-of-the-art computer vision models.

## Features

- **Real-time Detection**: Process video streams in real-time using YOLOv8, DETR, or YOLOS
- **Multi-Object Tracking**: Track multiple persons simultaneously with DeepSORT
- **Cross-Platform**: Works on desktop, tablet, and mobile devices
- **Web Interface**: Modern React frontend with live camera feed
- **WebSocket Support**: Low-latency real-time tracking
- **Multiple Models**: Choose between speed (YOLOv8) or accuracy (DETR)
- **GPU Acceleration**: CUDA and Apple Silicon support
- **Docker Ready**: Easy deployment with Docker Compose

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/person-movement-tracker.git
cd person-movement-tracker

# Start with Docker Compose
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download models
python ../scripts/download_models.py

# Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
person-movement-tracker/
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── models/       # AI model implementations
│   │   ├── api/          # API routes and schemas
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utilities
│   ├── tests/            # Unit tests
│   └── requirements.txt  # Python dependencies
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API services
│   │   └── utils/        # Utilities
│   └── package.json      # Node dependencies
├── scripts/              # Setup and utility scripts
├── docs/                 # Documentation
└── docker-compose.yml    # Docker configuration
```

## API Documentation

### REST API

- `POST /api/track` - Process image frame
- `GET /api/models` - List available models
- `GET /api/device` - Get device info
- `GET /health` - Health check

### WebSocket

- `WS /ws/track` - Real-time tracking stream

See [docs/API.md](docs/API.md) for detailed API documentation.

## Models

| Model | Speed | Accuracy | Size | Tracking |
|-------|-------|----------|------|----------|
| YOLOv8 | Fast | Good | 6MB | Yes |
| DETR | Medium | Excellent | 150MB | No |
| YOLOS | Medium | Good | 200MB | No |

## Configuration

### Environment Variables

**Backend (.env)**
```env
DEVICE=cpu                    # cpu, cuda, or mps
API_HOST=0.0.0.0
API_PORT=8000
CONFIDENCE_THRESHOLD=0.5
REDIS_URL=redis://localhost:6379
```

**Frontend (.env)**
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Deployment

### Docker Compose

```bash
docker-compose up -d
```

### Production

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment instructions.

### HuggingFace Spaces

```bash
# Deploy to HuggingFace Spaces
huggingface-cli login
./scripts/deploy.sh huggingface
```

## Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test

# Performance benchmark
python scripts/benchmark.py
```

## Performance

Benchmarks on CPU (Intel i7-10700):
- YOLOv8: ~30 FPS
- DETR: ~5 FPS
- Tracking: ~50 FPS

With GPU (RTX 3080):
- YOLOv8: ~100 FPS
- DETR: ~30 FPS

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [YOLOv8](https://github.com/ultralytics/ultralytics) by Ultralytics
- [DETR](https://github.com/facebookresearch/detr) by Facebook Research
- [DeepSORT](https://github.com/nwojke/deep_sort) for object tracking
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [React](https://reactjs.org/) for the frontend framework