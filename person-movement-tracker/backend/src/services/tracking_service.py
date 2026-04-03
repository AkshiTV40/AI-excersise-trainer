import asyncio
from typing import Dict, Any, Optional, List
import numpy as np
import cv2
import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor

try:
    from ..config import config
    from ..models.detector_factory import DetectorFactory, ModelType
    from ..models.tracker import MultiObjectTracker
    from ..utils.image_processor import ImageProcessor
except ImportError:
    from config import config
    from models.detector_factory import DetectorFactory, ModelType
    from models.tracker import MultiObjectTracker
    from utils.image_processor import ImageProcessor

class TrackingService:
    def __init__(self):
        self.detector = None
        self.tracker = None
        self.image_processor = ImageProcessor()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.sessions: Dict[str, TrackingSession] = {}
        
    async def initialize(self):
        """Initialize service with default detector"""
        self.detector = DetectorFactory.create_detector(
            config.default_model,
            device=str(config.device),
            confidence_threshold=config.confidence_threshold,
            iou_threshold=config.iou_threshold,
            enable_fp16=config.enable_fp16
        )
        
        self.tracker = MultiObjectTracker(
            tracker_type=config.tracker_type,
            max_age=config.max_track_age
        )
        
        # Warmup model
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self.detector.warmup)
        
        print(f"Tracking service initialized with {config.default_model}")
    
    async def process_frame(self, 
                          image_data: str, 
                          session_id: str,
                          model_type: Optional[ModelType] = None,
                          enable_tracking: bool = True) -> Dict[str, Any]:
        """Process a single frame"""
        try:
            # Decode image
            frame = await self.image_processor.decode_base64(image_data)
            
            # Resize based on device
            frame = self.image_processor.optimize_for_device(frame)
            
            # Run detection
            if model_type and model_type != config.default_model:
                # Use different detector for this request
                detector = DetectorFactory.create_detector(
                    model_type,
                    device=str(config.device),
                    confidence_threshold=config.confidence_threshold
                )
                result = await self._run_detection(detector, frame)
            else:
                result = await self._run_detection(self.detector, frame)
            
            # Apply tracking if enabled
            if enable_tracking and self.tracker:
                tracked_detections = await self._run_tracking(frame, result.detections)
                result.detections = tracked_detections
            
            # Encode result image
            output_frame = await self._draw_results(frame.copy(), result)
            encoded_image = await self.image_processor.encode_base64(output_frame)
            
            # Update session
            await self._update_session(session_id, result)
            
            return {
                'success': True,
                'image': encoded_image,
                'detections': self._detections_to_dict(result.detections),
                'inference_time': result.inference_time,
                'track_count': len([d for d in result.detections if d.track_id]),
                'model': result.model_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _run_detection(self, detector, frame: np.ndarray):
        """Run detection in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, detector.detect, frame)
    
    async def _run_tracking(self, frame: np.ndarray, detections: List):
        """Run tracking in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.tracker.update, 
            detections, frame
        )
    
    async def _draw_results(self, frame: np.ndarray, result) -> np.ndarray:
        """Draw detections and tracks on frame"""
        # Draw bounding boxes
        for det in result.detections:
            x1, y1, x2, y2 = map(int, det.bbox)
            color = (0, 255, 0) if det.track_id is None else (255, 0, 0)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{det.class_name} {det.confidence:.2f}"
            if det.track_id:
                label = f"ID:{det.track_id} {label}"
            
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw inference time
        cv2.putText(frame, f"Inference: {result.inference_time:.3f}s", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        return frame
    
    def _detections_to_dict(self, detections: List) -> List[Dict]:
        """Convert detections to JSON-serializable format"""
        return [{
            'bbox': det.bbox,
            'confidence': det.confidence,
            'class_id': det.class_id,
            'class_name': det.class_name,
            'track_id': det.track_id
        } for det in detections]
    
    async def _update_session(self, session_id: str, result):
        """Update session tracking data"""
        if session_id not in self.sessions:
            self.sessions[session_id] = TrackingSession(session_id)
        
        session = self.sessions[session_id]
        session.add_frame_result(result)

class TrackingSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = time.time()
        self.frame_results = []
        self.track_history = {}
    
    def add_frame_result(self, result):
        """Add frame result to session history"""
        self.frame_results.append({
            'timestamp': time.time(),
            'detection_count': len(result.detections),
            'inference_time': result.inference_time
        })
        
        # Update track history
        for det in result.detections:
            if det.track_id:
                if det.track_id not in self.track_history:
                    self.track_history[det.track_id] = []
                
                self.track_history[det.track_id].append({
                    'timestamp': time.time(),
                    'bbox': det.bbox,
                    'confidence': det.confidence
                })