# Deployment Guide

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [HuggingFace Spaces](#huggingface-spaces)

## Local Development

### Prerequisites
- Python 3.8+
- Node.js 18+
- Redis (optional, for session management)

### Backend Setup

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

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Docker Deployment

### Quick Start

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d
```

### Services

- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:3000`
- **Redis**: `localhost:6379`
- **Nginx**: `http://localhost:80`

### GPU Support

For GPU acceleration, ensure you have:
- NVIDIA Docker runtime installed
- NVIDIA drivers installed

```bash
# Start with GPU support
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up
```

## Production Deployment

### Environment Variables

Create a `.env` file in the project root:

```env
# Backend
DEVICE=cuda
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
REDIS_URL=redis://redis:6379

# Frontend
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
```

### SSL/TLS Configuration

1. Place SSL certificates in `ssl/` directory:
   - `ssl/cert.pem`
   - `ssl/key.pem`

2. Update `nginx.conf` with SSL configuration

### Scaling

For high-traffic deployments:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## HuggingFace Spaces

### Setup

1. Create a new Space on HuggingFace
2. Choose "Docker" as the SDK
3. Clone the repository:

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/person-movement-tracker
cd person-movement-tracker
```

4. Copy project files
5. Create `README.md`:

```markdown
---
title: Person Movement Tracker
emoji: 
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8000
---
```

6. Push to HuggingFace:

```bash
git add .
git commit -m "Initial commit"
git push
```

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000
```

### Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Local logs
tail -f backend/logs/app.log
tail -f frontend/logs/app.log
```

## Troubleshooting

### Common Issues

1. **CUDA out of memory**
   - Reduce `max_frame_size` in config
   - Use smaller model (yolov8n instead of yolov8l)
   - Reduce batch size

2. **Slow inference on CPU**
   - Enable model quantization
   - Reduce frame resolution
   - Use OpenVINO backend

3. **WebSocket connection failed**
   - Check CORS settings
   - Verify WebSocket URL
   - Check firewall rules

### Performance Optimization

1. **Enable GPU acceleration**
   ```env
   DEVICE=cuda
   ```

2. **Use Redis for session management**
   ```env
   REDIS_URL=redis://localhost:6379
   ```

3. **Enable FP16 (on supported GPUs)**
   ```env
   ENABLE_FP16=true
   ```

## Security Considerations

1. **Never commit `.env` files**
2. **Use strong API keys in production**
3. **Enable HTTPS for all communications**
4. **Implement rate limiting**
5. **Regular security updates**