"""YOLO Pose Detection Service

Uses YOLOv8 pose model for body landmark detection.

Note: This module focuses on *detection*.
Drawing skeleton connections should be done via:
  backend/src/utils/yolo_skeleton.py
for safety (no crashes).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

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
    """YOLO-based pose detector using YOLOv8 pose model.

    Detects 17 body keypoints for exercise form analysis.

    Keypoint order (17):
    0 nose
    1 left_eye
    2 right_eye
    3 left_ear
    4 right_ear
    5 left_shoulder
    6 right_shoulder
    7 left_elbow
    8 right_elbow
    9 left_wrist
    10 right_wrist
    11 left_hip
    12 right_hip
    13 left_knee
    14 right_knee
    15 left_ankle
    16 right_ankle
    """

    KEYPOINT_NAMES = [
        "nose",
        "left_eye",
        "right_eye",
        "left_ear",
        "right_ear",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
    ]

    def __init__(self, model_name: str = "yolov8n-pose.pt", device: str = "cpu"):
        if not YOLO_AVAILABLE:
            raise ImportError(
                "Ultralytics YOLO not installed. Install with: pip install ultralytics"
            )

        self.device = device
        self.model = None
        self.model_loaded = False
        self._load_model(model_name)

    def _load_model(self, model_name: str) -> None:
        try:
            self.model = YOLO(model_name)
            self.model.to(self.device)
            self.model_loaded = True
            logger.info(
                "YOLO pose model '%s' loaded successfully on %s", model_name, self.device
            )
        except Exception as e:
            self.model_loaded = False
            raise RuntimeError(f"Failed to load YOLO pose model: {e}")

    def detect(self, frame: np.ndarray) -> List[YOLOPoseResult]:
        """Detect pose keypoints in a frame."""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        results = self.model(frame, verbose=False)
        poses: List[YOLOPoseResult] = []

        if results and len(results) > 0:
            result = results[0]

            if result.keypoints is not None and len(result.keypoints.xy) > 0:
                keypoints_data = result.keypoints

                for person_idx in range(len(keypoints_data.xy)):
                    confidences = keypoints_data.conf[person_idx]
                    coords = keypoints_data.xy[person_idx]

                    keypoints: List[KeypointData] = []
                    for i, (x, y) in enumerate(coords):
                        if i >= len(self.KEYPOINT_NAMES):
                            break
                        conf = confidences[i].item() if i < len(confidences) else 0.0
                        keypoints.append(
                            KeypointData(x=float(x.item()), y=float(y.item()), confidence=float(conf))
                        )

                    if keypoints:
                        avg_conf = float(np.mean([k.confidence for k in keypoints]))
                        poses.append(YOLOPoseResult(keypoints=keypoints, confidence=avg_conf))

        return poses

    def extract_keypoints_dict(self, pose_result: YOLOPoseResult) -> Dict[str, Tuple[float, float]]:
        """Extract keypoints as a dictionary."""
        keypoints: Dict[str, Tuple[float, float]] = {}
        for i, kp in enumerate(pose_result.keypoints):
            if i < len(self.KEYPOINT_NAMES):
                keypoints[self.KEYPOINT_NAMES[i]] = (kp.x, kp.y)
        return keypoints

    def get_angle(
        self,
        keypoints: Dict[str, Tuple[float, float]],
        point1: str,
        point2: str,
        point3: str,
    ) -> float:
        """Calculate angle between three points."""
        if point1 not in keypoints or point2 not in keypoints or point3 not in keypoints:
            return 0.0

        p1 = np.array(keypoints[point1], dtype=float)
        p2 = np.array(keypoints[point2], dtype=float)
        p3 = np.array(keypoints[point3], dtype=float)

        v1 = p1 - p2
        v2 = p3 - p2

        denom = float(np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        cos_angle = float(np.dot(v1, v2) / denom)
        cos_angle = float(np.clip(cos_angle, -1.0, 1.0))
        angle = float(np.degrees(np.arccos(cos_angle)))
        return angle

    def cleanup(self) -> None:
        """Clean up resources."""
        self.model = None
        self.model_loaded = False

