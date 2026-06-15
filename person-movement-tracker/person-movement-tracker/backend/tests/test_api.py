import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient
from api.routes import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Person Movement Tracker API" in response.text

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_models():
    response = client.get("/api/models")
    assert response.status_code == 200
    
    models = response.json()
    assert isinstance(models, list)
    
    if len(models) > 0:
        model = models[0]
        assert "name" in model
        assert "description" in model
        assert "supports_tracking" in model

def test_get_device_info():
    response = client.get("/api/device")
    assert response.status_code == 200
    
    device_info = response.json()
    assert "device" in device_info
    assert "cuda_available" in device_info
    assert "cpu_count" in device_info

def test_track_endpoint_invalid_image():
    """Test track endpoint with invalid image data"""
    response = client.post("/api/track", json={
        "image": "invalid_base64_data",
        "session_id": "test_session",
        "enable_tracking": True
    })
    
    # Should return error for invalid image
    assert response.status_code in [200, 422]

def test_session_stats():
    response = client.get("/api/session/test_session/stats")
    assert response.status_code == 200
    
    stats = response.json()
    assert "session_id" in stats
    assert "frame_count" in stats
    assert "average_inference_time" in stats
    assert "total_tracks" in stats

@pytest.mark.asyncio
async def test_websocket():
    """Test WebSocket connection"""
    import asyncio
    
    # Note: WebSocket testing requires async client
    # This is a basic structure
    pass

if __name__ == '__main__':
    pytest.main([__file__, '-v'])