"""YOLO pose skeleton drawing helpers.

This module is designed to be robust (no crashes):
- validates array sizes
- guards against NaN/inf
- clamps drawing to frame bounds
- applies confidence thresholds
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import math

import cv2
import numpy as np


# Your YOLO wrapper outputs 17 keypoints in this order:
# 0: nose
# 1: left_eye
# 2: right_eye
# 3: left_ear
# 4: right_ear
# 5: left_shoulder
# 6: right_shoulder
# 7: left_elbow
# 8: right_elbow
# 9: left_wrist
# 10: right_wrist
# 11: left_hip
# 12: right_hip
# 13: left_knee
# 14: right_knee
# 15: left_ankle
# 16: right_ankle

# Reasonable skeleton connections for 17 keypoints.
YOLO_17_CONNECTIONS: List[Tuple[int, int]] = [
    (5, 7),   # left shoulder -> left elbow
    (7, 9),   # left elbow -> left wrist
    (6, 8),   # right shoulder -> right elbow
    (8, 10),  # right elbow -> right wrist
    (11, 13), # left hip -> left knee
    (13, 15), # left knee -> left ankle
    (12, 14), # right hip -> right knee
    (14, 16), # right knee -> right ankle
    (5, 6),   # left shoulder -> right shoulder
    (11, 12), # left hip -> right hip
    (5, 11),  # left shoulder -> left hip
    (6, 12),  # right shoulder -> right hip
]


def _is_finite_number(x: float) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def draw_yolo_17_skeleton(
    frame: np.ndarray,
    keypoints_xy: Sequence[Sequence[float]],
    keypoints_conf: Optional[Sequence[float]] = None,
    *,
    conf_threshold: float = 0.4,
    line_color: Tuple[int, int, int] = (0, 255, 0),
    point_color: Tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2,
    point_radius: int = 2,
) -> np.ndarray:
    """Draw skeleton given YOLO 17 keypoints.

    Crash-proof:
    - accepts malformed/missing keypoints
    - guards NaN/inf for both coords and confidences
    - validates keypoint structure per-item
    - clamps drawing within frame bounds

    Note: keypoints_xy is expected as pixel coords (x,y), but this function
    tolerates unexpected shapes by simply skipping invalid points.
    """

    if frame is None:
        return frame

    if keypoints_xy is None:
        return frame

    h, w = frame.shape[:2]

    pts: List[Tuple[int, int]] = []
    confs: List[float] = []

    for i, kp in enumerate(keypoints_xy):
        if kp is None or len(kp) < 2:
            pts.append((0, 0))
            confs.append(0.0)
            continue
        x, y = kp[0], kp[1]
        if not _is_finite_number(x) or not _is_finite_number(y):
            pts.append((0, 0))
            confs.append(0.0)
            continue

        xi = int(x)
        yi = int(y)
        xi = _clamp(xi, 0, w - 1)
        yi = _clamp(yi, 0, h - 1)
        pts.append((xi, yi))

        if keypoints_conf is not None and i < len(keypoints_conf):
            c = float(keypoints_conf[i])
            confs.append(c if _is_finite_number(c) else 0.0)
        else:
            confs.append(1.0)  # if unknown, draw

    # Draw connections
    for a, b in YOLO_17_CONNECTIONS:
        if a >= len(pts) or b >= len(pts):
            continue
        if confs[a] < conf_threshold or confs[b] < conf_threshold:
            continue
        pt1 = pts[a]
        pt2 = pts[b]
        cv2.line(frame, pt1, pt2, line_color, thickness)

    # Draw points
    for idx, (x, y) in enumerate(pts):
        if idx >= len(confs):
            c = 1.0
        else:
            c = confs[idx]
        if c < conf_threshold:
            continue
        if _is_finite_number(x) and _is_finite_number(y):
            cv2.circle(frame, (int(x), int(y)), point_radius, point_color, -1)

    return frame

