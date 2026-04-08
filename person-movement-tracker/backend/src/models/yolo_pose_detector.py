"""
YOLO Pose Detection Service
Uses YOLOv8 pose model for body landmark detection
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import cv2

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class KeypointData:
    """Data class for a single keypoint"""
    x: float
    y: float
    confidence: float


@dataclass
class YOLOPoseResult:
    """Result from YOLO pose detection"""
    keypoints: List[KeypointData]
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None


class YOLOPoseDetector:
    """
    YOLO-based pose detector using YOLOv8 pose model
    Detects 17 body keypoints for exercise form analysis
    """
    
    KEYPOINT_NAMES = [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ]
    
    def __init__(self, model_name: str = "yolov8n-pose.pt", device: str = "cpu"):
        """
        Initialize YOLO pose detector
        
        Args:
            model_name: YOLO model name (yolov8n-pose, yolov8s-pose, etc.)
            device: Device to run on ('cpu' or 'cuda')
        """
        if not YOLO_AVAILABLE:
            raise ImportError(
                "Ultralytics YOLO not installed. Install with: pip install ultralytics"
            )
        
        self.device = device
        self.model = None
        self.model_loaded = False
        self._load_model(model_name)
    
    def _load_model(self, model_name: str) -> None:
        """Load the YOLO pose model"""
        try:
            self.model = YOLO(model_name)
            self.model.to(self.device)
            self.model_loaded = True
            logger.info(f"YOLO pose model '{model_name}' loaded successfully on {self.device}")
        except Exception as e:
            self.model_loaded = False
            raise RuntimeError(f"Failed to load YOLO pose model: {e}")
    
    def detect(self, frame: np.ndarray) -> List[YOLOPoseResult]:
        """
        Detect pose keypoints in a frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of YOLOPoseResult (one per person detected)
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")
        
        results = self.model(frame, verbose=False)
        
        poses = []
        
        if results and len(results) > 0:
            result = results[0]
            
            if result.keypoints is not None and len(result.keypoints.xy) > 0:
                keypoints_data = result.keypoints
                
                for person_idx in range(len(keypoints_data.xy)):
                    keypoints = []
                    confidences = keypoints_data.conf[person_idx]
                    coords = keypoints_data.xy[person_idx]
                    
                    for i, (x, y) in enumerate(coords):
                        if i < len(self.KEYPOINT_NAMES):
                            conf = confidences[i].item() if i < len(confidences) else 0.0
                            keypoints.append(KeypointData(
                                x=float(x.item()),
                                y=float(y.item()),
                                confidence=float(conf)
                            ))
                    
                    if keypoints:
                        avg_conf = np.mean([k.confidence for k in keypoints])
                        poses.append(YOLOPoseResult(
                            keypoints=keypoints,
                            confidence=float(avg_conf)
                        ))
        
        return poses
    
    def detect_with_visualization(self, frame: np.ndarray) -> Tuple[np.ndarray, List[YOLOPoseResult]]:
        """
        Detect poses and draw keypoints/skeleton on the frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Tuple of (annotated frame, pose results)
        """
        results = self.model(frame, verbose=False)
        poses = []
        
        if results and len(results) > 0:
            result = results[0]
            
            annotated_frame = result.plot()
            
            if result.keypoints is not None and len(result.keypoints.xy) > 0:
                keypoints_data = result.keypoints
                
                for person_idx in range(len(keypoints_data.xy)):
                    keypoints = []
                    confidences = keypoints_data.conf[person_idx]
                    coords = keypoints_data.xy[person_idx]
                    
                    for i, (x, y) in enumerate(coords):
                        if i < len(self.KEYPOINT_NAMES):
                            conf = confidences[i].item() if i < len(confidences) else 0.0
                            keypoints.append(KeypointData(
                                x=float(x.item()),
                                y=float(y.item()),
                                confidence=float(conf)
                            ))
                    
                    if keypoints:
                        avg_conf = np.mean([k.confidence for k in keypoints])
                        poses.append(YOLOPoseResult(
                            keypoints=keypoints,
                            confidence=float(avg_conf)
                        ))
        
        return annotated_frame, poses
    
    def extract_keypoints_dict(self, pose_result: YOLOPoseResult) -> Dict[str, Tuple[float, float]]:
        """
        Extract keypoints as a dictionary
        
        Args:
            pose_result: YOLO pose detection result
            
        Returns:
            Dictionary of keypoint names to (x, y) coordinates
        """
        keypoints = {}
        for i, kp in enumerate(pose_result.keypoints):
            if i < len(self.KEYPOINT_NAMES):
                keypoints[self.KEYPOINT_NAMES[i]] = (kp.x, kp.y)
        return keypoints
    
    def get_angle(self, keypoints: Dict[str, Tuple[float, float]], 
                  point1: str, point2: str, point3: str) -> float:
        """
        Calculate angle between three points
        
        Args:
            keypoints: Dictionary of keypoint names to (x, y) coordinates
            point1: First point name
            point2: Middle point name (vertex)
            point3: Third point name
            
        Returns:
            Angle in degrees
        """
        if point1 not in keypoints or point2 not in keypoints or point3 not in keypoints:
            return 0.0
        
        p1 = np.array(keypoints[point1])
        p2 = np.array(keypoints[point2])
        p3 = np.array(keypoints[point3])
        
        v1 = p1 - p2
        v2 = p3 - p2
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.degrees(np.arccos(cos_angle))
        
        return float(angle)
    
    def cleanup(self) -> None:
        """Clean up resources"""
        self.model = None
        self.model_loaded = False