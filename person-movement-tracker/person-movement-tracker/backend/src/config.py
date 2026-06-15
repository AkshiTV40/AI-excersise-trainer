from pydantic_settings import BaseSettings
from typing import List, Optional, Tuple
from enum import Enum
import json

class ModelType(str, Enum):
    YOLOv8 = "yolov8"
    DETR = "detr"
    YOLOS = "yolos"
    FASTERRCNN = "fasterrcnn"

class DeviceType(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # For Apple Silicon

class AppConfig(BaseSettings):
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    cors_origins: List[str] = ["*"]
    
    # Model Settings
    default_model: ModelType = ModelType.YOLOv8
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    
    # Device Settings
    device: DeviceType = DeviceType.CPU
    max_batch_size: int = 4
    frame_skip: int = 1
    
    # Tracking Settings
    max_track_age: int = 30
    min_track_confidence: float = 0.3
    tracker_type: str = "deepsort"  # "deepsort", "bytetrack", "botsort"
    
    # Redis for session management
    redis_url: str = "redis://localhost:6379"
    
    # HuggingFace
    hf_token: Optional[str] = None
    hf_cache_dir: str = "./models"
    
    # Performance
    max_frame_size: str = "[1280,720]"
    mobile_frame_size: str = "[640,480]"
    enable_fp16: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse string tuples back to actual tuples (handle format like "[1280,720]")
        if isinstance(self.max_frame_size, str):
            # Remove brackets and split by comma
            cleaned = self.max_frame_size.strip('[]')
            self.max_frame_size = tuple(map(int, cleaned.split(',')))
        if isinstance(self.mobile_frame_size, str):
            # Remove brackets and split by comma
            cleaned = self.mobile_frame_size.strip('[]')
            self.mobile_frame_size = tuple(map(int, cleaned.split(',')))

config = AppConfig()