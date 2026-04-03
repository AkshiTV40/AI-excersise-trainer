import torch
import numpy as np
from typing import List, Tuple, Any
from ultralytics import YOLO
import cv2

try:
    from .base_detector import BaseDetector, Detection
except ImportError:
    from models.base_detector import BaseDetector, Detection

class YOLODetector(BaseDetector):
    def __init__(self, model_path: str = 'yolov8n.pt', **kwargs):
        super().__init__(model_name=model_path, **kwargs)
        self.model_path = model_path
        self.load_model()
    
    def load_model(self):
        """Load YOLO model"""
        print(f"Loading YOLO model: {self.model_path}")
        self._model = YOLO(self.model_path)
        
        # Move to device
        self._model.to(self.device)
        
        # YOLO class names
        self.class_names = self._model.names if hasattr(self._model, 'names') else ['person']
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """YOLO handles preprocessing internally"""
        return frame
    
    def predict(self, processed_input: Any) -> Any:
        """Run YOLO inference"""
        results = self._model(
            processed_input,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False,
            max_det=50
        )
        return results
    
    def postprocess(self, predictions: Any, frame_shape: Tuple[int, int]) -> List[Detection]:
        """Convert YOLO results to detections"""
        detections = []
        
        if predictions and len(predictions) > 0:
            result = predictions[0]
            
            if result.boxes is not None:
                boxes = result.boxes.cpu().numpy()
                
                for box in boxes:
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    detections.append(Detection(
                        bbox=[x1, y1, x2, y2],
                        confidence=conf,
                        class_id=cls,
                        class_name=self.class_names.get(cls, f"class_{cls}")
                    ))
        
        return detections
    
    def track(self, frame: np.ndarray, persist: bool = True) -> List[Detection]:
        """Run YOLO with tracking"""
        results = self._model.track(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            persist=persist,
            verbose=False,
            max_det=50
        )
        
        detections = []
        if results and len(results) > 0:
            result = results[0]
            
            if result.boxes is not None and result.boxes.id is not None:
                boxes = result.boxes.cpu().numpy()
                track_ids = result.boxes.id.cpu().numpy()
                
                for box, track_id in zip(boxes, track_ids):
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    detections.append(Detection(
                        bbox=[x1, y1, x2, y2],
                        confidence=conf,
                        class_id=cls,
                        class_name=self.class_names.get(cls, f"class_{cls}"),
                        track_id=int(track_id)
                    ))
        
        return detections