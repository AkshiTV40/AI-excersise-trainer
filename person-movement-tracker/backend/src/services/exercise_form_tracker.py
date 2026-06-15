"""Exercise form tracker (video-based): compare user video vs reference video.

Implements the pipeline described in EXERCISE_FORM_TRACKER_DIFF_PLAN.md:
A) ingest + sampling
B) YOLOv8 pose extraction
C) stabilize keypoints (confidence filtering + EMA smoothing)
D) align moments using dynamic time warping (DTW) on feature time series
E) compute delta features + summary
F) optional visualization overlays

This module is designed to be imported and used by FastAPI routes.
"""

from __future__ import annotations

import logging
import math
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from ..models.yolo_pose_detector import YOLOPoseDetector, YOLOPoseResult
from ..utils.yolo_skeleton import draw_yolo_17_skeleton

logger = logging.getLogger(__name__)


# --- Core data model ---


@dataclass
class PoseFrameKeypoints:
    keypoints_xy: List[Tuple[float, float]]  # 17 points
    keypoints_conf: List[float]  # 17 points
    total_conf: float


@dataclass
class PoseFrameFeatures:
    # Feature vector for a single frame.
    # Order is stable and used for DTW distance.
    vec: np.ndarray
    # Useful individual scalars for reporting.
    scalars: Dict[str, float]


@dataclass
class DeltaMetrics:
    mean_abs_deltas: Dict[str, float]
    max_abs_deltas: Dict[str, float]
    worst_feature_deltas: Dict[str, float]
    percent_exceeds: Dict[str, float]


# --- Utilities ---


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _safe_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle ABC in degrees."""
    # vectors BA and BC
    v1 = a - b
    v2 = c - b
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-6 or n2 < 1e-6:
        return 0.0
    cosang = float(np.dot(v1, v2) / (n1 * n2))
    cosang = _clamp(cosang, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))


def _ema(prev: np.ndarray, cur: np.ndarray, alpha: float) -> np.ndarray:
    if prev is None:
        return cur
    return alpha * cur + (1.0 - alpha) * prev


def _best_pose(poses: Sequence[YOLOPoseResult]) -> Optional[YOLOPoseResult]:
    if not poses:
        return None
    return max(poses, key=lambda p: float(p.confidence) if p and p.confidence is not None else 0.0)


def _poses_to_frame_keypoints(pose: YOLOPoseResult, expected_kps: int = 17) -> PoseFrameKeypoints:
    keypoints_xy = []
    keypoints_conf = []
    # YOLOPoseDetector uses KEYPOINT_NAMES length (16?); however YOLOPoseResult.keypoints should match its KEYPOINT_NAMES.
    # We still enforce expected_kps by padding.
    for kp in pose.keypoints:
        keypoints_xy.append((float(kp.x), float(kp.y)))
        keypoints_conf.append(float(kp.confidence))

    # pad / trim
    if len(keypoints_xy) < expected_kps:
        for _ in range(expected_kps - len(keypoints_xy)):
            keypoints_xy.append((0.0, 0.0))
            keypoints_conf.append(0.0)
    elif len(keypoints_xy) > expected_kps:
        keypoints_xy = keypoints_xy[:expected_kps]
        keypoints_conf = keypoints_conf[:expected_kps]

    total_conf = float(np.mean(keypoints_conf)) if keypoints_conf else 0.0
    return PoseFrameKeypoints(
        keypoints_xy=keypoints_xy,
        keypoints_conf=keypoints_conf,
        total_conf=total_conf,
    )


def _filter_keypoints_by_conf(
    frame_kps: PoseFrameKeypoints, min_conf: float
) -> PoseFrameKeypoints:
    kps_xy = []
    kps_conf = []
    for (x, y), c in zip(frame_kps.keypoints_xy, frame_kps.keypoints_conf):
        if float(c) < min_conf:
            kps_xy.append((0.0, 0.0))
            kps_conf.append(0.0)
        else:
            kps_xy.append((x, y))
            kps_conf.append(float(c))

    total_conf = float(np.mean(kps_conf)) if kps_conf else 0.0
    return PoseFrameKeypoints(keypoints_xy=kps_xy, keypoints_conf=kps_conf, total_conf=total_conf)


# --- Motion score & sampling ---


def compute_motion_score(prev_gray: np.ndarray, gray: np.ndarray) -> float:
    """Simple motion score based on mean absolute difference."""
    diff = cv2.absdiff(gray, prev_gray)
    return float(np.mean(diff))


def sample_video_frames(
    video_path: str,
    *,
    max_frames: int = 120,
    sample_rate_hz: float = 2.0,
    motion_select: bool = True,
    motion_top_k: int = 60,
    upscale: Optional[Tuple[int, int]] = (640, 480),
) -> Tuple[List[np.ndarray], List[float]]:
    """Return frames and timestamps.

    motion_select: if True, run pose extraction only on motion peaks
    by selecting top-k by motion score.
    """

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    fps = float(fps)

    # compute interval between reads
    interval = max(1, int(round(fps / sample_rate_hz)))

    frames: List[np.ndarray] = []
    timestamps: List[float] = []
    motion_scores: List[float] = []
    idxs: List[int] = []

    frame_idx = 0
    prev_gray = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % interval == 0:
            if upscale is not None:
                frame = cv2.resize(frame, upscale)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if prev_gray is None:
                score = 0.0
            else:
                score = compute_motion_score(prev_gray, gray)

            prev_gray = gray

            frames.append(frame)
            timestamps.append(frame_idx / fps)
            motion_scores.append(score)
            idxs.append(len(frames) - 1)

        frame_idx += 1
        if len(frames) >= max_frames * 2:  # allow extra for motion selection
            # We will trim after selection.
            break

    cap.release()

    if not frames:
        raise ValueError(f"No frames extracted from video: {video_path}")

    if not motion_select:
        # keep first max_frames
        return frames[:max_frames], timestamps[:max_frames]

    # Select top-k motion frames
    k = min(motion_top_k, len(frames))
    order = np.argsort(motion_scores)[::-1]
    selected_idx = sorted(order[:k])

    sel_frames = [frames[i] for i in selected_idx]
    sel_timestamps = [timestamps[i] for i in selected_idx]

    return sel_frames, sel_timestamps


# --- Feature extraction ---


def yolo_17_to_names() -> List[str]:
    # Must match YOLOPoseDetector.KEYPOINT_NAMES order.
    return [
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


def extract_feature_vector(
    kps_xy: List[Tuple[float, float]],
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Extract exercise-agnostic feature vector from 17 keypoints.

    Indices based on yolo_17_to_names.
    """
    names = yolo_17_to_names()
    kp_map = {n: kps_xy[i] for i, n in enumerate(names) if i < len(kps_xy)}

    def pt(name: str) -> np.ndarray:
        return np.array(kp_map.get(name, (0.0, 0.0)), dtype=np.float32)

    # Angles (provide depth proxy via hip height relationship).
    # Angles:
    # - elbows: shoulder-elbow-wrist
    # - knees: hip-knee-ankle
    # - hips: shoulder-hip-knee
    left_elbow_ang = _safe_angle(pt("left_shoulder"), pt("left_elbow"), pt("left_wrist"))
    right_elbow_ang = _safe_angle(pt("right_shoulder"), pt("right_elbow"), pt("right_wrist"))
    left_knee_ang = _safe_angle(pt("left_hip"), pt("left_knee"), pt("left_ankle"))
    right_knee_ang = _safe_angle(pt("right_hip"), pt("right_knee"), pt("right_ankle"))
    left_hip_ang = _safe_angle(pt("left_shoulder"), pt("left_hip"), pt("left_knee"))
    right_hip_ang = _safe_angle(pt("right_shoulder"), pt("right_hip"), pt("right_knee"))

    # Symmetry: elbow/knee angle differences
    elbow_sym = abs(left_elbow_ang - right_elbow_ang)
    knee_sym = abs(left_knee_ang - right_knee_ang)
    hip_sym = abs(left_hip_ang - right_hip_ang)

    # Depth proxy: compare hip y to shoulder y (larger forward/down in image -> larger delta)
    # In image coords, y increases downward.
    left_depth = float(pt("left_hip")[1] - pt("left_shoulder")[1])
    right_depth = float(pt("right_hip")[1] - pt("right_shoulder")[1])
    depth = (left_depth + right_depth) / 2.0

    scalars = {
        "left_elbow_angle": left_elbow_ang,
        "right_elbow_angle": right_elbow_ang,
        "left_knee_angle": left_knee_ang,
        "right_knee_angle": right_knee_ang,
        "left_hip_angle": left_hip_ang,
        "right_hip_angle": right_hip_ang,
        "elbow_symmetry": elbow_sym,
        "knee_symmetry": knee_sym,
        "hip_symmetry": hip_sym,
        "depth_proxy": depth,
    }

    # Vector order matters for DTW distance.
    vec = np.array(
        [
            left_elbow_ang,
            right_elbow_ang,
            left_knee_ang,
            right_knee_ang,
            left_hip_ang,
            right_hip_ang,
            elbow_sym,
            knee_sym,
            hip_sym,
            depth,
        ],
        dtype=np.float32,
    )

    # Normalize-ish to stable scales (angles ~0-180, depth in pixels)
    # We'll just scale depth down to a reasonable range.
    vec[-1] = vec[-1] / 100.0

    return vec, scalars


# --- DTW ---


def dtw_align(
    seq_a: np.ndarray,
    seq_b: np.ndarray,
    *,
    dist_p: int = 2,
    max_warping_window: Optional[int] = None,
) -> Tuple[float, List[Tuple[int, int]]]:
    """Dynamic Time Warping alignment.

    seq_a: (Ta, D)
    seq_b: (Tb, D)

    Returns: (cost, path_indices)
    """
    Ta, Da = seq_a.shape
    Tb, Db = seq_b.shape
    if Da != Db:
        raise ValueError("DTW sequences must have same feature dimension")

    if max_warping_window is None:
        max_warping_window = max(Ta, Tb)

    w = max_warping_window

    # cost matrix with inf
    D = np.full((Ta + 1, Tb + 1), np.inf, dtype=np.float64)
    D[0, 0] = 0.0

    # backpointers
    ptr = np.zeros((Ta + 1, Tb + 1, 2), dtype=np.int32)

    for i in range(1, Ta + 1):
        j_start = max(1, i - w)
        j_end = min(Tb, i + w)
        for j in range(j_start, j_end + 1):
            # distance
            diff = np.abs(seq_a[i - 1] - seq_b[j - 1])
            if dist_p == 1:
                cost = float(np.sum(diff))
            else:
                cost = float(np.linalg.norm(diff, ord=2))

            candidates = [
                (D[i - 1, j], (i - 1, j)),
                (D[i, j - 1], (i, j - 1)),
                (D[i - 1, j - 1], (i - 1, j - 1)),
            ]
            best_prev = min(candidates, key=lambda x: x[0])
            D[i, j] = best_prev[0] + cost
            ptr[i, j] = best_prev[1]

    # Backtrack
    i, j = Ta, Tb
    path: List[Tuple[int, int]] = []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        ni, nj = int(ptr[i, j][0]), int(ptr[i, j][1])
        i, j = ni, nj

    path.reverse()
    return float(D[Ta, Tb]), path


# --- Public tracker ---


class ExerciseFormTracker:
    def __init__(
        self,
        *,
        yolo_model_name: str = "yolov8n-pose.pt",
        device: str = "cpu",
        min_pose_conf: float = 0.35,
        ema_alpha: float = 0.6,
    ):
        self.pose_detector = YOLOPoseDetector(model_name=yolo_model_name, device=device)
        self.min_pose_conf = float(min_pose_conf)
        self.ema_alpha = float(ema_alpha)

    def _extract_sequence_keypoints(self, frames: List[np.ndarray]) -> List[PoseFrameKeypoints]:
        out: List[PoseFrameKeypoints] = []
        for idx, frame in enumerate(frames):
            poses = self.pose_detector.detect(frame)
            best = _best_pose(poses)
            if best is None or best.confidence < self.min_pose_conf:
                # empty frame => zeroed keypoints but keep length
                kps_xy = [(0.0, 0.0)] * 17
                kps_conf = [0.0] * 17
                out.append(PoseFrameKeypoints(kps_xy, kps_conf, 0.0))
                continue

            out.append(_poses_to_frame_keypoints(best, expected_kps=17))
        return out

    def _stabilize_keypoints(
        self, seq: List[PoseFrameKeypoints]
    ) -> List[PoseFrameKeypoints]:
        """Confidence filtering + EMA smoothing on xy coordinates."""
        stabilized: List[PoseFrameKeypoints] = []
        prev_xy = None
        prev_conf = None

        for frame in seq:
            filtered = _filter_keypoints_by_conf(frame, min_conf=self.min_pose_conf)
            xy = np.array(filtered.keypoints_xy, dtype=np.float32)  # (17,2)
            conf = np.array(filtered.keypoints_conf, dtype=np.float32)

            if prev_xy is None:
                smooth_xy = xy
            else:
                smooth_xy = _ema(prev_xy, xy, self.ema_alpha)

            prev_xy = smooth_xy
            prev_conf = conf

            stabilized.append(
                PoseFrameKeypoints(
                    keypoints_xy=[(float(xy[i, 0]), float(xy[i, 1])) for i in range(17)],
                    keypoints_conf=[float(conf[i]) for i in range(17)],
                    total_conf=float(np.mean(conf)) if len(conf) else 0.0,
                )
            )

        return stabilized

    def _sequence_to_features(
        self, seq: List[PoseFrameKeypoints]
    ) -> Tuple[np.ndarray, List[PoseFrameFeatures]]:
        vecs: List[np.ndarray] = []
        feats: List[PoseFrameFeatures] = []
        for frame in seq:
            vec, scalars = extract_feature_vector(frame.keypoints_xy)
            vecs.append(vec)
            feats.append(PoseFrameFeatures(vec=vec, scalars=scalars))
        return np.stack(vecs, axis=0), feats

    def compare_videos(
        self,
        *,
        reference_video_path: str,
        user_video_path: str,
        max_frames: int = 120,
        sample_rate_hz: float = 2.0,
        motion_select: bool = True,
        motion_top_k: int = 60,
        upscale: Optional[Tuple[int, int]] = (640, 480),
        delta_exceed_threshold: float = 0.25,
        save_overlays: bool = False,
        overlays_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 1) sample
        ref_frames, ref_ts = sample_video_frames(
            reference_video_path,
            max_frames=max_frames,
            sample_rate_hz=sample_rate_hz,
            motion_select=motion_select,
            motion_top_k=motion_top_k,
            upscale=upscale,
        )
        user_frames, user_ts = sample_video_frames(
            user_video_path,
            max_frames=max_frames,
            sample_rate_hz=sample_rate_hz,
            motion_select=motion_select,
            motion_top_k=motion_top_k,
            upscale=upscale,
        )

        # 2) pose extraction
        ref_seq = self._extract_sequence_keypoints(ref_frames)
        user_seq = self._extract_sequence_keypoints(user_frames)

        # 3) stabilize
        ref_seq_s = self._stabilize_keypoints(ref_seq)
        user_seq_s = self._stabilize_keypoints(user_seq)

        # 4) features
        ref_vecs, ref_feats = self._sequence_to_features(ref_seq_s)
        user_vecs, user_feats = self._sequence_to_features(user_seq_s)

        # 5) DTW align
        _, path = dtw_align(ref_vecs, user_vecs, max_warping_window=max(len(ref_frames), len(user_frames)))

        # 6) delta metrics
        feature_names = [
            "left_elbow_angle",
            "right_elbow_angle",
            "left_knee_angle",
            "right_knee_angle",
            "left_hip_angle",
            "right_hip_angle",
            "elbow_symmetry",
            "knee_symmetry",
            "hip_symmetry",
            "depth_proxy",
        ]

        # Build aligned scalar arrays
        aligned_ref = []
        aligned_user = []
        for i_ref, i_user in path:
            aligned_ref.append(ref_feats[i_ref].scalars)
            aligned_user.append(user_feats[i_user].scalars)

        # Compute deltas per feature
        mean_abs_deltas: Dict[str, float] = {}
        max_abs_deltas: Dict[str, float] = {}
        worst_feature_deltas: Dict[str, float] = {}
        percent_exceeds: Dict[str, float] = {}

        # We'll compute delta on raw scalars, but depth is in pixels so scaling is hard.
        # We accept delta_exceed_threshold on normalized vector components instead.
        # So we compute exceed using feature vectors.
        aligned_ref_vec = ref_vecs[[i for i, _ in path]]
        aligned_user_vec = user_vecs[[j for _, j in path]]

        abs_delta_vec = np.abs(aligned_user_vec - aligned_ref_vec)

        for feat_idx, name in enumerate(feature_names):
            vals = abs_delta_vec[:, feat_idx]
            mean_abs_deltas[name] = float(np.mean(vals))
            max_abs_deltas[name] = float(np.max(vals))
            worst_feature_deltas[name] = float(np.max(vals))
            percent_exceeds[name] = float(np.mean(vals > delta_exceed_threshold) * 100.0)

        # Determine overall severity by mean abs delta across features
        severity_score = float(np.mean(abs_delta_vec))
        overall_status = (
            "EXCELLENT" if severity_score < 0.10 else
            "GOOD" if severity_score < 0.20 else
            "NEEDS IMPROVEMENT" if severity_score < 0.35 else
            "POOR"
        )

        report: Dict[str, Any] = {
            "overall_status": overall_status,
            "severity_score": severity_score,
            "num_ref_frames": len(ref_frames),
            "num_user_frames": len(user_frames),
            "dtw_path_length": len(path),
            "mean_abs_deltas": mean_abs_deltas,
            "max_abs_deltas": max_abs_deltas,
            "percent_exceeds": percent_exceeds,
            "worst_feature": max(max_abs_deltas.items(), key=lambda kv: kv[1])[0] if max_abs_deltas else None,
        }

        # 7) optional overlays (save skeleton on worst aligned frames)
        if save_overlays:
            if overlays_dir is None:
                overlays_dir = tempfile.mkdtemp(prefix="form_tracker_overlays_")
            os.makedirs(overlays_dir, exist_ok=True)

            # worst frame index by overall abs delta magnitude
            magnitudes = np.mean(abs_delta_vec, axis=1)
            worst_k = 5
            worst_order = np.argsort(magnitudes)[::-1][:worst_k]

            overlay_paths: List[str] = []
            for rank, pidx in enumerate(worst_order):
                i_ref, i_user = path[pidx]
                # Use original frames in lists (already upscaled)
                ref_frame = ref_frames[i_ref].copy()
                user_frame = user_frames[i_user].copy()

                # draw skeletons using stabilized keypoints
                ref_kps = ref_seq_s[i_ref]
                user_kps = user_seq_s[i_user]

                ref_frame = draw_yolo_17_skeleton(
                    ref_frame,
                    ref_kps.keypoints_xy,
                    ref_kps.keypoints_conf,
                    conf_threshold=self.min_pose_conf,
                )
                user_frame = draw_yolo_17_skeleton(
                    user_frame,
                    user_kps.keypoints_xy,
                    user_kps.keypoints_conf,
                    conf_threshold=self.min_pose_conf,
                )

                out_path = os.path.join(overlays_dir, f"overlay_rank_{rank+1}_refidx_{i_ref}_useridx_{i_user}.png")
                # side-by-side
                concat = cv2.hconcat([ref_frame, user_frame])
                cv2.imwrite(out_path, concat)
                overlay_paths.append(out_path)

            report["overlay_paths"] = overlay_paths

        return report

