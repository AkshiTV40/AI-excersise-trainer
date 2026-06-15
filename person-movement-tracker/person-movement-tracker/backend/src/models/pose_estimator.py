"""
Pose Estimation Model using MediaPipe
Provides body landmark detection for exercise form analysis
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import cv2

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

from .base_detector import BaseDetector


class PoseLandmarks:
    """Data class for pose landmarks"""
    
    def __init__(self, landmarks: List[Dict[str, float]], confidence: float = 0.0):
        self.landmarks = landmarks  # List of {x, y, z, visibility}
        self.confidence = confidence
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "landmarks": self.landmarks,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }


class MediaPipePoseDetector:
    """
    MediaPipe Pose detector for body landmark detection
    Detects 33 body landmarks for comprehensive pose analysis
    """
    
    # MediaPipe landmark indices
    LANDMARKS = {
        "nose": 0,
        "left_eye_inner": 1,
        "left_eye": 2,
        "left_eye_outer": 3,
        "right_eye_inner": 4,
        "right_eye": 5,
        "right_eye_outer": 6,
        "left_ear": 7,
        "right_ear": 8,
        "mouth_left": 9,
        "mouth_right": 10,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_pinky": 17,
        "right_pinky": 18,
        "left_index": 19,
        "right_index": 20,
        "left_thumb": 21,
        "right_thumb": 22,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
        "left_heel": 29,
        "right_heel": 30,
        "left_foot_index": 31,
        "right_foot_index": 32
    }
    
    def __init__(self, model_complexity: int = 1, min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5, device: str = "cpu"):
        """
        Initialize MediaPipe Pose detector
        
        Args:
            model_complexity: Model complexity (0, 1, or 2)
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            device: Device to run on (cpu or cuda)
        """
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError(
                "MediaPipe is not installed. Install it with: pip install mediapipe"
            )
        
        self.device = device
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = None
        self.model_loaded = False
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the MediaPipe Pose model"""
        try:
            self.pose = self.mp_pose.Pose(
                model_complexity=self.model_complexity,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
                static_image_mode=False
            )
            self.model_loaded = True
        except Exception as e:
            self.model_loaded = False
            raise RuntimeError(f"Failed to load MediaPipe Pose model: {e}")
    
    def detect(self, frame: np.ndarray) -> List[PoseLandmarks]:
        """
        Detect pose landmarks in a frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of PoseLandmarks (one per person detected)
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        results = self.pose.process(rgb_frame)
        
        poses = []
        
        if results.pose_landmarks:
            # Extract landmarks
            landmarks = self._extract_landmarks(results.pose_landmarks)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(results.pose_landmarks)
            
            poses.append(PoseLandmarks(landmarks, confidence))
        
        return poses
    
    def _extract_landmarks(self, pose_landmarks) -> List[Dict[str, float]]:
        """
        Extract landmarks from MediaPipe result
        
        Args:
            pose_landmarks: MediaPipe pose landmarks
            
        Returns:
            List of landmark dictionaries with x, y, z, visibility
        """
        landmarks = []
        
        for idx, landmark in enumerate(pose_landmarks.landmark):
            landmarks.append({
                "id": idx,
                "name": self._get_landmark_name(idx),
                "x": float(landmark.x),
                "y": float(landmark.y),
                "z": float(landmark.z),
                "visibility": float(landmark.visibility)
            })
        
        return landmarks
    
    def _get_landmark_name(self, idx: int) -> str:
        """Get the name of a landmark by index"""
        for name, index in self.LANDMARKS.items():
            if index == idx:
                return name
        return f"landmark_{idx}"
    
    def _calculate_confidence(self, pose_landmarks) -> float:
        """
        Calculate overall confidence from landmarks
        
        Args:
            pose_landmarks: MediaPipe pose landmarks
            
        Returns:
            Average visibility score
        """
        visibilities = [lm.visibility for lm in pose_landmarks.landmark]
        return float(np.mean(visibilities))
    
    def draw_landmarks(self, frame: np.ndarray, pose_landmarks: PoseLandmarks,
                      draw_connections: bool = True) -> np.ndarray:
        """
        Draw pose landmarks on frame
        
        Args:
            frame: Input frame
            pose_landmarks: Pose landmarks to draw
            draw_connections: Whether to draw connections between landmarks
            
        Returns:
            Frame with landmarks drawn
        """
        if not self.model_loaded:
            return frame
        
        # Convert landmarks back to MediaPipe format
        mp_landmarks = self._convert_to_mediapipe_landmarks(pose_landmarks.landmarks)
        
        # Create a normalized landmark list
        landmark_list = self.mp_pose.PoseLandmark
        
        # Draw landmarks
        if draw_connections:
            self.mp_drawing.draw_landmarks(
                frame,
                mp_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )
        else:
            for landmark in pose_landmarks.landmarks:
                x = int(landmark["x"] * frame.shape[1])
                y = int(landmark["y"] * frame.shape[0])
                cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
        
        return frame
    
    def _convert_to_mediapipe_landmarks(self, landmarks: List[Dict[str, float]]):
        """Convert landmarks to MediaPipe format for drawing"""
        # This is a simplified conversion
        # In practice, you'd need to create proper NormalizedLandmarkList
        return None
    
    def get_keypoints(self, pose_landmarks: PoseLandmarks) -> Dict[str, Tuple[float, float]]:
        """
        Extract key body points as coordinates
        
        Args:
            pose_landmarks: Pose landmarks
            
        Returns:
            Dictionary of keypoint names to (x, y) coordinates
        """
        keypoints = {}
        
        for landmark in pose_landmarks.landmarks:
            name = landmark["name"]
            x = landmark["x"]
            y = landmark["y"]
            keypoints[name] = (x, y)
        
        return keypoints
    
    def get_angle(self, pose_landmarks: PoseLandmarks, point1: str, point2: str, point3: str) -> float:
        """
        Calculate the angle between three points
        
        Args:
            pose_landmarks: Pose landmarks
            point1: First point name (e.g., "left_shoulder")
            point2: Middle point name (e.g., "left_elbow")
            point3: Third point name (e.g., "left_wrist")
            
        Returns:
            Angle in degrees
        """
        keypoints = self.get_keypoints(pose_landmarks)
        
        if point1 not in keypoints or point2 not in keypoints or point3 not in keypoints:
            return 0.0
        
        p1 = np.array(keypoints[point1])
        p2 = np.array(keypoints[point2])
        p3 = np.array(keypoints[point3])
        
        # Calculate vectors
        v1 = p1 - p2
        v2 = p3 - p2
        
        # Calculate angle
        angle = np.degrees(np.arccos(
            np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        ))
        
        return angle
    
    def get_distance(self, pose_landmarks: PoseLandmarks, point1: str, point2: str) -> float:
        """
        Calculate the distance between two points
        
        Args:
            pose_landmarks: Pose landmarks
            point1: First point name
            point2: Second point name
            
        Returns:
            Normalized distance
        """
        keypoints = self.get_keypoints(pose_landmarks)
        
        if point1 not in keypoints or point2 not in keypoints:
            return 0.0
        
        p1 = np.array(keypoints[point1])
        p2 = np.array(keypoints[point2])
        
        return float(np.linalg.norm(p1 - p2))
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.pose:
            self.pose.close()
        self.model_loaded = False
