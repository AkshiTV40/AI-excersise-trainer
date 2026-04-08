"""
Background Form Detection Service
Combines YOLO pose detection with exercise form classification
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np
import cv2

from ..models.yolo_pose_detector import YOLOPoseDetector, YOLOPoseResult
from ..services.exercise_form_classifier import ExerciseFormClassifier, FormClassificationResult

logger = logging.getLogger(__name__)


@dataclass
class BackgroundAnalysisResult:
    """Result from background form analysis"""
    form_classification: Optional[FormClassificationResult]
    keypoints: Dict[str, tuple]
    angles: Dict[str, float]
    timestamp: float
    frame_idx: int


class BackgroundFormDetector:
    """
    Service for detecting exercise form in background processing
    Uses YOLO for pose detection and XGBoost classifier for form analysis
    """
    
    def __init__(self, 
                 yolo_model: str = "yolov8n-pose.pt",
                 classifier_model: Optional[str] = None,
                 device: str = "cpu"):
        """
        Initialize the background form detector
        
        Args:
            yolo_model: YOLO model name
            classifier_model: Path to trained classifier model
            device: Device to run on ('cpu' or 'cuda')
        """
        self.yolo_detector = None
        self.classifier = None
        self.device = device
        
        self._initialize(yolo_model, classifier_model)
    
    def _initialize(self, yolo_model: str, classifier_model: Optional[str]):
        """Initialize YOLO detector and classifier"""
        try:
            self.yolo_detector = YOLOPoseDetector(model_name=yolo_model, device=self.device)
            logger.info("YOLO pose detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize YOLO detector: {e}")
            raise
        
        try:
            self.classifier = ExerciseFormClassifier(model_path=classifier_model)
            if classifier_model:
                logger.info(f"Loaded classifier from {classifier_model}")
            else:
                logger.info("Using heuristic mode for form classification")
        except Exception as e:
            logger.warning(f"Classifier initialization warning: {e}")
            self.classifier = None
    
    def analyze_frame(self, frame: np.ndarray, frame_idx: int = 0) -> BackgroundAnalysisResult:
        """
        Analyze a single frame for form detection
        
        Args:
            frame: Input frame
            frame_idx: Frame index
            
        Returns:
            BackgroundAnalysisResult with analysis data
        """
        keypoints = {}
        angles = {}
        classification = None
        
        if self.yolo_detector is None:
            return BackgroundAnalysisResult(
                form_classification=None,
                keypoints=keypoints,
                angles=angles,
                timestamp=time.time(),
                frame_idx=frame_idx
            )
        
        try:
            pose_results = self.yolo_detector.detect(frame)
            
            if pose_results and len(pose_results) > 0:
                pose = pose_results[0]
                keypoints = self.yolo_detector.extract_keypoints_dict(pose)
                
                angles = self._calculate_angles(keypoints)
                
                if self.classifier:
                    classification = self.classifier.predict(keypoints)
        
        except Exception as e:
            logger.error(f"Error analyzing frame {frame_idx}: {e}")
        
        return BackgroundAnalysisResult(
            form_classification=classification,
            keypoints=keypoints,
            angles=angles,
            timestamp=time.time(),
            frame_idx=frame_idx
        )
    
    def _calculate_angles(self, keypoints: Dict[str, tuple]) -> Dict[str, float]:
        """Calculate key angles for form analysis"""
        angles = {}
        
        if not keypoints:
            return angles
        
        if all(k in keypoints for k in ["left_shoulder", "left_elbow", "left_wrist"]):
            angles["left_elbow"] = self.yolo_detector.get_angle(
                keypoints, "left_shoulder", "left_elbow", "left_wrist"
            )
        
        if all(k in keypoints for k in ["right_shoulder", "right_elbow", "right_wrist"]):
            angles["right_elbow"] = self.yolo_detector.get_angle(
                keypoints, "right_shoulder", "right_elbow", "right_wrist"
            )
        
        if all(k in keypoints for k in ["left_hip", "left_knee", "left_ankle"]):
            angles["left_knee"] = self.yolo_detector.get_angle(
                keypoints, "left_hip", "left_knee", "left_ankle"
            )
        
        if all(k in keypoints for k in ["right_hip", "right_knee", "right_ankle"]):
            angles["right_knee"] = self.yolo_detector.get_angle(
                keypoints, "right_hip", "right_knee", "right_ankle"
            )
        
        if all(k in keypoints for k in ["left_shoulder", "left_hip", "left_knee"]):
            angles["left_hip"] = self.yolo_detector.get_angle(
                keypoints, "left_shoulder", "left_hip", "left_knee"
            )
        
        if all(k in keypoints for k in ["right_shoulder", "right_hip", "right_knee"]):
            angles["right_hip"] = self.yolo_detector.get_angle(
                keypoints, "right_shoulder", "right_hip", "right_knee"
            )
        
        return angles
    
    def analyze_video_frames(self, frames: List[np.ndarray], 
                              skip_frames: int = 1) -> List[BackgroundAnalysisResult]:
        """
        Analyze multiple frames from a video
        
        Args:
            frames: List of video frames
            skip_frames: Process every nth frame
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i in range(0, len(frames), skip_frames):
            result = self.analyze_frame(frames[i], frame_idx=i)
            results.append(result)
        
        return results
    
    def get_aggregate_analysis(self, results: List[BackgroundAnalysisResult]) -> Dict[str, Any]:
        """
        Get aggregate analysis from multiple frame results
        
        Args:
            results: List of frame analysis results
            
        Returns:
            Dictionary with aggregated metrics
        """
        if not results:
            return {"status": "no_data"}
        
        good_form_count = 0
        bad_form_count = 0
        total_confidence = 0.0
        valid_results = 0
        
        for result in results:
            if result.form_classification:
                valid_results += 1
                if result.form_classification.is_good_form:
                    good_form_count += 1
                else:
                    bad_form_count += 1
                total_confidence += result.form_classification.confidence
        
        if valid_results == 0:
            return {
                "status": "no_detections",
                "frames_analyzed": len(results)
            }
        
        avg_confidence = total_confidence / valid_results
        good_form_ratio = good_form_count / valid_results
        
        if good_form_ratio >= 0.7:
            status = "GOOD_FORM"
        elif good_form_ratio >= 0.4:
            status = "NEEDS_IMPROVEMENT"
        else:
            status = "BAD_FORM"
        
        return {
            "status": status,
            "frames_analyzed": len(results),
            "valid_detections": valid_results,
            "good_form_count": good_form_count,
            "bad_form_count": bad_form_count,
            "good_form_ratio": round(good_form_ratio, 2),
            "average_confidence": round(avg_confidence, 2),
            "recommendation": self._get_recommendation(status, good_form_ratio)
        }
    
    def _get_recommendation(self, status: str, good_ratio: float) -> str:
        """Get recommendation based on analysis status"""
        recommendations = {
            "GOOD_FORM": "Great form! Keep maintaining proper technique.",
            "NEEDS_IMPROVEMENT": "Focus on improving form consistency. Watch for common mistakes.",
            "BAD_FORM": "Please review proper form. Consider reducing weight or consulting a trainer."
        }
        return recommendations.get(status, "Continue practicing.")
    
    def cleanup(self):
        """Clean up resources"""
        if self.yolo_detector:
            self.yolo_detector.cleanup()
            self.yolo_detector = None