"""
Video Analysis Service
Analyzes video frames to detect exercises and provide form feedback
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
import cv2
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FrameAnalysis:
    """Analysis result for a single frame"""
    frame_number: int
    timestamp: float
    people_detected: int
    poses: List[Dict]
    issues: List[Dict]
    exercise_type: Optional[str] = None
    form_score: float = 0.0


@dataclass
class VideoAnalysisResult:
    """Complete analysis result for a video"""
    total_frames: int
    analyzed_frames: int
    duration: float
    fps: float
    detected_exercise: Optional[str] = None
    overall_form_score: float = 0.0
    frame_analyses: List[Dict] = None
    summary: Dict = None
    
    def __post_init__(self):
        if self.frame_analyses is None:
            self.frame_analyses = []
        if self.summary is None:
            self.summary = {}


class VideoAnalysisService:
    """Service for analyzing video frames"""
    
    def __init__(self, pose_detector, exercise_analyzer):
        """
        Initialize video analysis service
        
        Args:
            pose_detector: Pose detection model
            exercise_analyzer: Exercise analysis model
        """
        self.pose_detector = pose_detector
        self.exercise_analyzer = exercise_analyzer
        self.analysis_results = []
    
    async def analyze_frames(self, frames: List[np.ndarray], 
                           exercise_type: Optional[str] = None,
                           callback=None,
                           fps: float = 30.0) -> VideoAnalysisResult:
        """
        Analyze multiple video frames
        
        Args:
            frames: List of frame arrays
            exercise_type: Optional exercise type to analyze for
            callback: Optional callback function for progress updates
            
        Returns:
            VideoAnalysisResult with analysis data
        """
        try:
            total_frames = len(frames)
            frame_analyses = []
            form_scores = []
            detected_exercises = {}
            issues_summary = {"critical": 0, "warning": 0, "info": 0}
            
            for idx, frame in enumerate(frames):
                # Detect poses in frame
                poses, confidence = self._detect_poses(frame)
                
                # Analyze exercise form if poses detected
                issues = []
                form_score = 100.0
                
                if poses and exercise_type:
                    issues, form_score = self._analyze_exercise_form(
                        poses, exercise_type, frame
                    )
                    
                    # Track exercise detection
                    if exercise_type not in detected_exercises:
                        detected_exercises[exercise_type] = 0
                    detected_exercises[exercise_type] += 1
                    
                    # Accumulate scores
                    form_scores.append(form_score)
                
                # Count issue severity
                for issue in issues:
                    severity = issue.get("severity", "info").lower()
                    if severity in issues_summary:
                        issues_summary[severity] += 1
                
                # Create frame analysis
                frame_analysis = {
                    "frame_number": idx,
                    "timestamp": idx / fps,  # Use actual video FPS
                    "people_detected": len(poses) if poses else 0,
                    "poses": self._format_poses(poses),
                    "issues": issues,
                    "form_score": form_score if poses else 0.0,
                    "exercise_type": exercise_type
                }
                
                frame_analyses.append(frame_analysis)
                
                # Progress callback
                if callback:
                    progress = (idx + 1) / total_frames * 100
                    await callback({
                        "progress": progress,
                        "current_frame": idx + 1,
                        "total_frames": total_frames,
                        "people_detected": len(poses) if poses else 0
                    })
            
            # Calculate overall results
            overall_form_score = np.mean(form_scores) if form_scores else 0.0
            detected_exercise = exercise_type if form_scores else None
            
            # Create summary
            summary = self._create_summary(
                frame_analyses, 
                overall_form_score, 
                issues_summary,
                detected_exercise
            )
            
            result = VideoAnalysisResult(
                total_frames=total_frames,
                analyzed_frames=len(frame_analyses),
                duration=total_frames / fps,
                fps=fps,
                detected_exercise=detected_exercise,
                overall_form_score=overall_form_score,
                frame_analyses=frame_analyses,
                summary=summary
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing frames: {str(e)}")
            raise

    async def analyze_video_file(self, video_path: str, exercise_type: Optional[str] = None, max_seconds: int = 10,
                                 sample_rate: float = 2.0, callback=None) -> VideoAnalysisResult:
        """Analyze a local video file by sampling frames"""
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            max_frames = min(total_frames, int(max_seconds * fps)) if total_frames > 0 else int(max_seconds * fps)
            frame_interval = max(1, int(fps // sample_rate))

            frames = []
            frame_idx = 0
            collected = 0

            while cap.isOpened() and collected < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    # Resize and normalize
                    frame_resized = cv2.resize(frame, (640, 480))
                    frames.append(frame_resized)
                    collected += 1

                frame_idx += 1

            if not frames:
                raise ValueError("No frames extracted from video file")

            analysis_result = await self.analyze_frames(frames, exercise_type=exercise_type, callback=callback, fps=fps)
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing video file: {str(e)}")
            raise

        finally:
            if cap is not None:
                cap.release()
    
    def _detect_poses(self, frame: np.ndarray) -> tuple:
        """
        Detect poses in a frame
        
        Args:
            frame: Image frame
            
        Returns:
            Tuple of (poses_list, confidence)
        """
        try:
            pose_landmarks_list = self.pose_detector.detect(frame)
            
            if not pose_landmarks_list:
                return [], 0.0
            
            poses = []
            total_confidence = 0.0
            
            for pose_landmarks in pose_landmarks_list:
                pose_data = []
                for landmark in pose_landmarks.landmarks:
                    pose_data.append({
                        "id": landmark.get("id"),
                        "x": landmark["x"],
                        "y": landmark["y"],
                        "z": landmark.get("z", 0.0),
                        "visibility": landmark.get("visibility", 1.0)
                    })
                
                poses.append({
                    "landmarks": pose_data,
                    "confidence": pose_landmarks.confidence
                })
                total_confidence += pose_landmarks.confidence
            
            avg_confidence = total_confidence / len(poses) if poses else 0.0
            return poses, avg_confidence
            
        except Exception as e:
            logger.error(f"Error detecting poses: {str(e)}")
            return [], 0.0
    
    def _analyze_exercise_form(self, poses: List[Dict], 
                               exercise_type: str,
                               frame: np.ndarray) -> tuple:
        """
        Analyze exercise form in detected poses
        
        Args:
            poses: List of detected poses
            exercise_type: Type of exercise to analyze
            frame: Original frame for analysis
            
        Returns:
            Tuple of (issues_list, form_score)
        """
        try:
            issues = []
            form_score = 100.0
            
            if not poses:
                return issues, 0.0
            
            # Get landmarks from first pose
            landmarks = poses[0].get("landmarks", [])
            if not landmarks:
                return issues, 0.0
            
            # Analyze based on exercise type
            if exercise_type.lower() == "squat":
                issues, score = self._analyze_squat(landmarks)
            elif exercise_type.lower() == "pushup":
                issues, score = self._analyze_pushup(landmarks)
            elif exercise_type.lower() == "lunge":
                issues, score = self._analyze_lunge(landmarks)
            elif exercise_type.lower() == "plank":
                issues, score = self._analyze_plank(landmarks)
            else:
                # Generic analysis
                issues, score = self._generic_exercise_analysis(landmarks)
            
            return issues, score
            
        except Exception as e:
            logger.error(f"Error analyzing exercise form: {str(e)}")
            return [], 0.0
    
    def _analyze_squat(self, landmarks: List[Dict]) -> tuple:
        """Analyze squat form"""
        issues = []
        score = 100.0
        
        try:
            # Key points for squat analysis
            # 0: nose, 11: left shoulder, 12: right shoulder
            # 23: left hip, 24: right hip, 25: left knee, 26: right knee
            
            if len(landmarks) < 27:
                return issues, 0.0
            
            # Check if knees go past toes
            left_ankle = landmarks[27] if len(landmarks) > 27 else landmarks[25]
            right_ankle = landmarks[28] if len(landmarks) > 28 else landmarks[26]
            left_knee = landmarks[25]
            right_knee = landmarks[26]
            
            # Verify knee angle (simplified check)
            if left_knee['y'] > left_ankle['y'] - 0.1:
                issues.append({
                    "severity": "warning",
                    "message": "Left knee extends too far forward",
                    "suggestion": "Keep knees behind toes for safer form"
                })
                score -= 15
            
            # Check back alignment
            left_shoulder = landmarks[11]
            left_hip = landmarks[23]
            if abs(left_shoulder['x'] - left_hip['x']) > 0.15:
                issues.append({
                    "severity": "warning",
                    "message": "Back is not properly aligned",
                    "suggestion": "Keep your back straight and core engaged"
                })
                score -= 10
            
            # Check depth
            hip_to_knee = abs(landmarks[23]['y'] - landmarks[25]['y'])
            if hip_to_knee > 0.3:
                issues.append({
                    "severity": "info",
                    "message": "Squat depth could be deeper",
                    "suggestion": "Try to lower hips further for full range of motion"
                })
                score -= 5
            
        except Exception as e:
            logger.error(f"Error in squat analysis: {str(e)}")
        
        return issues, max(score, 0.0)
    
    def _analyze_pushup(self, landmarks: List[Dict]) -> tuple:
        """Analyze pushup form"""
        issues = []
        score = 100.0
        
        try:
            if len(landmarks) < 27:
                return issues, 0.0
            
            # Check body alignment
            shoulder = landmarks[11]
            hip = landmarks[23]
            knee = landmarks[25] if len(landmarks) > 25 else landmarks[24]
            
            # Verify straight body line
            shoulder_hip_diff = abs(shoulder['y'] - hip['y'])
            if shoulder_hip_diff > 0.2:
                issues.append({
                    "severity": "critical",
                    "message": "Body is not properly aligned",
                    "suggestion": "Keep your body in a straight line from head to heels"
                })
                score -= 25
            
            # Check elbow angle
            shoulder_z = shoulder.get('z', 0)
            if shoulder_z > 0.1:
                issues.append({
                    "severity": "warning",
                    "message": "Elbows may not be tucked properly",
                    "suggestion": "Keep elbows close to your body"
                })
                score -= 10
            
        except Exception as e:
            logger.error(f"Error in pushup analysis: {str(e)}")
        
        return issues, max(score, 0.0)
    
    def _analyze_lunge(self, landmarks: List[Dict]) -> tuple:
        """Analyze lunge form"""
        issues = []
        score = 100.0
        
        try:
            if len(landmarks) < 27:
                return issues, 0.0
            
            # Check knee alignment
            left_knee = landmarks[25]
            right_knee = landmarks[26]
            left_ankle = landmarks[27] if len(landmarks) > 27 else landmarks[25]
            
            # Front knee should be above ankle
            if left_knee['y'] < left_ankle['y'] - 0.05:
                issues.append({
                    "severity": "warning",
                    "message": "Front knee extends past ankle",
                    "suggestion": "Adjust position so knee is directly above ankle"
                })
                score -= 15
            
            # Check back alignment
            left_shoulder = landmarks[11]
            left_hip = landmarks[23]
            if abs(left_shoulder['x'] - left_hip['x']) > 0.1:
                issues.append({
                    "severity": "info",
                    "message": "Try to keep your torso upright",
                    "suggestion": "Engage your core and maintain upright posture"
                })
                score -= 5
            
        except Exception as e:
            logger.error(f"Error in lunge analysis: {str(e)}")
        
        return issues, max(score, 0.0)
    
    def _analyze_plank(self, landmarks: List[Dict]) -> tuple:
        """Analyze plank form"""
        issues = []
        score = 100.0
        
        try:
            if len(landmarks) < 27:
                return issues, 0.0
            
            # Check body alignment
            shoulder = landmarks[11]
            hip = landmarks[23]
            knee = landmarks[25]
            ankle = landmarks[27] if len(landmarks) > 27 else landmarks[25]
            
            # All should be in roughly same line
            shoulder_hip_diff = abs(shoulder['y'] - hip['y'])
            hip_knee_diff = abs(hip['y'] - knee['y'])
            
            if shoulder_hip_diff > 0.15 or hip_knee_diff > 0.15:
                issues.append({
                    "severity": "critical",
                    "message": "Hips are sagging or too high",
                    "suggestion": "Keep hips in line with shoulders and heels for proper plank form"
                })
                score -= 30
            
            # Check head position
            nose = landmarks[0]
            if nose['y'] < shoulder['y'] - 0.1:
                issues.append({
                    "severity": "info",
                    "message": "Head position could be better",
                    "suggestion": "Keep your head neutral, looking slightly ahead"
                })
                score -= 5
            
        except Exception as e:
            logger.error(f"Error in plank analysis: {str(e)}")
        
        return issues, max(score, 0.0)
    
    def _generic_exercise_analysis(self, landmarks: List[Dict]) -> tuple:
        """Generic exercise analysis for unknown types"""
        issues = []
        score = 75.0
        
        try:
            # Check overall pose quality
            visibility_scores = [l.get('visibility', 0) for l in landmarks if 'visibility' in l]
            
            if visibility_scores:
                avg_visibility = np.mean(visibility_scores)
                if avg_visibility < 0.5:
                    issues.append({
                        "severity": "warning",
                        "message": "Poor pose visibility",
                        "suggestion": "Try to be more visible to the camera"
                    })
                    score -= 20
            
        except Exception as e:
            logger.error(f"Error in generic analysis: {str(e)}")
        
        return issues, max(score, 0.0)
    
    def _format_poses(self, poses: List[Dict]) -> List[Dict]:
        """Format poses for JSON serialization"""
        formatted = []
        for pose in poses:
            formatted.append({
                "landmarks": pose.get("landmarks", []),
                "confidence": pose.get("confidence", 0.0)
            })
        return formatted
    
    def _create_summary(self, frame_analyses: List[Dict],
                       overall_score: float,
                       issues_summary: Dict,
                       exercise_type: Optional[str]) -> Dict:
        """Create analysis summary"""
        
        frames_with_people = sum(1 for f in frame_analyses if f['people_detected'] > 0)
        avg_form_score = np.mean([f['form_score'] for f in frame_analyses if f['form_score'] > 0]) if frame_analyses else 0.0
        
        # Determine recommendations
        recommendations = []
        if issues_summary['critical'] > 0:
            recommendations.append("⚠️ CRITICAL: Address form issues before continuing with this exercise")
        if issues_summary['warning'] > frames_with_people * 0.5:
            recommendations.append("⚠️ Focus on improving form consistency")
        if avg_form_score < 70:
            recommendations.append("📚 Consider reviewing proper exercise technique")
        else:
            recommendations.append("✅ Good form! Keep practicing to maintain consistency")
        
        # Determine overall status
        if overall_score >= 85:
            status = "EXCELLENT"
        elif overall_score >= 70:
            status = "GOOD"
        elif overall_score >= 50:
            status = "NEEDS IMPROVEMENT"
        else:
            status = "POOR - MAJOR CORRECTIONS NEEDED"
        
        return {
            "status": status,
            "overall_form_score": round(overall_score, 2),
            "frames_with_people": frames_with_people,
            "total_frames": len(frame_analyses),
            "critical_issues": issues_summary['critical'],
            "warnings": issues_summary['warning'],
            "info_messages": issues_summary['info'],
            "exercise_type": exercise_type,
            "recommendations": recommendations
        }
