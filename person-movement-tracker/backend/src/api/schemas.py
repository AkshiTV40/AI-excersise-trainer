from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class ModelType(str, Enum):
    YOLOv8 = "yolov8"
    DETR = "detr"
    YOLOS = "yolos"

class ExerciseType(str, Enum):
    SQUAT = "squat"
    PUSHUP = "pushup"
    LUNGE = "lunge"
    PLANK = "plank"
    DEADLIFT = "deadlift"
    BENCH_PRESS = "bench_press"
    OVERHEAD_PRESS = "overhead_press"
    BICEP_CURL = "bicep_curl"
    TRICEP_EXTENSION = "tricep_extension"
    JUMPING_JACK = "jumping_jack"

class TrackingRequest(BaseModel):
    image: str
    session_id: str
    model_type: Optional[ModelType] = None
    enable_tracking: bool = True

class ExerciseTrackingRequest(BaseModel):
    image: str
    session_id: str
    exercise_type: ExerciseType
    enable_tracking: bool = True

class DetectionResult(BaseModel):
    bbox: List[float]
    confidence: float
    class_id: int
    class_name: str
    track_id: Optional[int] = None

class PoseLandmark(BaseModel):
    id: int
    name: str
    x: float
    y: float
    z: float
    visibility: float

class PoseData(BaseModel):
    landmarks: List[PoseLandmark]
    confidence: float
    timestamp: float

class FormIssue(BaseModel):
    severity: str
    message: str
    suggestion: str
    affected_landmarks: List[str] = []
    timestamp: float

class ExerciseAnalysis(BaseModel):
    exercise: str
    rep_count: int
    state: str
    angles: Dict[str, float]
    form_issues: List[FormIssue] = []
    feedback: List[str] = []

class TrackingResponse(BaseModel):
    success: bool
    image: Optional[str] = None
    detections: List[DetectionResult] = []
    inference_time: float = 0.0
    track_count: int = 0
    model: str = ""
    error: Optional[str] = None

class ExerciseTrackingResponse(BaseModel):
    success: bool
    image: Optional[str] = None
    pose_data: Optional[PoseData] = None
    analysis: Optional[ExerciseAnalysis] = None
    inference_time: float = 0.0
    error: Optional[str] = None

class ModelInfo(BaseModel):
    name: str
    description: str
    supports_tracking: bool

class DeviceInfo(BaseModel):
    device: str
    cuda_available: bool
    mps_available: bool = False
    cpu_count: int
    cuda_device_count: Optional[int] = None
    cuda_device_name: Optional[str] = None

class SessionStats(BaseModel):
    session_id: str
    frame_count: int
    average_inference_time: float
    total_tracks: int

class TrackHistory(BaseModel):
    track_id: int
    timestamps: List[float]
    bboxes: List[List[float]]
    confidences: List[float]

class SessionData(BaseModel):
    session_id: str
    start_time: float
    frame_results: List[Dict[str, Any]]
    track_history: Dict[int, List[Dict[str, Any]]]