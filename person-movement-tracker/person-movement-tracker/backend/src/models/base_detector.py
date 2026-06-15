import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

import numpy as np

@dataclass
class Detection:
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str
    track_id: Optional[int] = None

@dataclass
class ModelResult:
    detections: List[Detection]
    inference_time: float
    frame_shape: Tuple[int, int]
    model_name: str

class BaseDetector(ABC):
    def __init__(self, model_name: str, device: str = "cpu", **kwargs):
        self.model_name = model_name
        self.device = device
        self.confidence_threshold = kwargs.get('confidence_threshold', 0.5)
        self.iou_threshold = kwargs.get('iou_threshold', 0.45)
        self.class_names = kwargs.get('class_names', ['person'])
        self._model = None
        
    @abstractmethod
    def load_model(self):
        """Load the model"""
        pass
    
    @abstractmethod
    def preprocess(self, frame: np.ndarray) -> Any:
        """Preprocess input frame"""
        pass
    
    @abstractmethod
    def predict(self, processed_input: Any) -> Any:
        """Run inference"""
        pass
    
    @abstractmethod
    def postprocess(self, predictions: Any, frame_shape: Tuple[int, int]) -> List[Detection]:
        """Convert predictions to detections"""
        pass
    
    def detect(self, frame: np.ndarray) -> ModelResult:
        """Complete detection pipeline"""
        start_time = time.time()
        
        # Preprocess
        processed = self.preprocess(frame)
        
        # Predict
        predictions = self.predict(processed)
        
        # Postprocess
        detections = self.postprocess(predictions, frame.shape[:2])
        
        inference_time = time.time() - start_time
        
        return ModelResult(
            detections=detections,
            inference_time=inference_time,
            frame_shape=frame.shape[:2],
            model_name=self.model_name
        )
    
    def filter_detections(self, detections: List[Detection], 
                         class_filter: Optional[List[int]] = None) -> List[Detection]:
        """Filter detections by confidence and class"""
        filtered = []
        for det in detections:
            if det.confidence >= self.confidence_threshold:
                if class_filter is None or det.class_id in class_filter:
                    filtered.append(det)
        return filtered
    
    def warmup(self, iterations: int = 10):
        """Warmup the model with dummy data"""
        dummy_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        for _ in range(iterations):
            _ = self.detect(dummy_frame)