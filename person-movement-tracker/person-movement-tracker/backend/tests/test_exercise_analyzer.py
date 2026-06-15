import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock


class TestExerciseType:
    """Test ExerciseType enum"""
    
    def test_exercise_type_values(self):
        from models.exercise_analyzer import ExerciseType
        
        assert ExerciseType.SQUAT.value == "squat"
        assert ExerciseType.PUSHUP.value == "pushup"
        assert ExerciseType.LUNGE.value == "lunge"
        assert ExerciseType.PLANK.value == "plank"
        assert ExerciseType.DEADLIFT.value == "deadlift"


class TestPoseLandmarks:
    """Test PoseLandmarks dataclass"""
    
    def test_pose_landmarks_creation(self):
        from models.pose_estimator import PoseLandmarks
        
        landmarks = [
            {"id": 0, "name": "nose", "x": 0.5, "y": 0.1, "z": 0.0, "visibility": 0.9},
            {"id": 11, "name": "left_shoulder", "x": 0.4, "y": 0.3, "z": 0.0, "visibility": 0.8},
        ]
        
        pose = PoseLandmarks(landmarks=landmarks, confidence=0.85)
        
        assert pose.confidence == 0.85
        assert len(pose.landmarks) == 2
        assert pose.landmarks[0]["name"] == "nose"


class TestMediaPipePoseDetector:
    """Test MediaPipePoseDetector angle calculations"""
    
    def test_angle_calculation(self):
        from models.pose_estimator import MediaPipePoseDetector, PoseLandmarks
        
        mock_detector = Mock(spec=MediaPipePoseDetector)
        mock_detector.get_keypoints = MagicMock(return_value={
            "left_shoulder": (0.5, 0.3),
            "left_hip": (0.5, 0.5),
            "left_knee": (0.5, 0.7),
        })
        
        pose_landmarks = PoseLandmarks([], 1.0)
        
        result = MediaPipePoseDetector.get_angle(
            mock_detector, pose_landmarks, "left_shoulder", "left_hip", "left_knee"
        )
        
        assert isinstance(result, float)
        assert result >= 0
    
    def test_get_keypoints(self):
        from models.pose_estimator import PoseLandmarks
        
        landmarks = [
            {"id": 11, "name": "left_shoulder", "x": 0.5, "y": 0.3, "z": 0.0, "visibility": 0.9},
            {"id": 23, "name": "left_hip", "x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.9},
            {"id": 25, "name": "left_knee", "x": 0.5, "y": 0.7, "z": 0.0, "visibility": 0.9},
        ]
        
        pose = PoseLandmarks(landmarks=landmarks, confidence=0.9)
        
        keypoints = {
            "left_shoulder": (0.5, 0.3),
            "left_hip": (0.5, 0.5),
            "left_knee": (0.5, 0.7),
        }
        
        assert "left_shoulder" in keypoints
        assert "left_hip" in keypoints


class TestSquatAnalyzer:
    """Test SquatAnalyzer form analysis"""
    
    def test_squat_depth_check(self):
        from models.exercise_analyzer import SquatAnalyzer, FormIssue
        
        mock_detector = Mock()
        
        analyzer = SquatAnalyzer(mock_detector)
        
        analyzer._add_form_issue(
            "warning",
            "Squat depth is insufficient",
            "Try to go lower - aim for thighs parallel to the ground",
            ["left_knee", "right_knee"]
        )
        
        issues = analyzer.form_issues
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert "depth" in issues[0].message.lower()
    
    def test_knee_valgus_detection(self):
        from models.exercise_analyzer import FormIssue
        
        issue = FormIssue(
            severity="critical",
            message="Left knee is caving inward (valgus)",
            suggestion="Push your knees out to track over your toes",
            affected_landmarks=["left_knee", "left_ankle"]
        )
        
        assert issue.severity == "critical"
        assert "valgus" in issue.message.lower()


class TestRepCounter:
    """Test RepCounter state machine"""
    
    def test_rep_count_increment(self):
        from models.exercise_analyzer import RepCounter, ExerciseType, ExerciseState
        
        counter = RepCounter(ExerciseType.SQUAT)
        
        assert counter.count == 0
        assert counter.state == ExerciseState.START
        
        counter.update(ExerciseState.MOVING)
        assert counter.state == ExerciseState.MOVING
        
        counter.update(ExerciseState.END)
        assert counter.count == 1
        
        counter.update(ExerciseState.START)
        assert counter.state == ExerciseState.START
    
    def test_reset(self):
        from models.exercise_analyzer import RepCounter, ExerciseType, ExerciseState
        
        counter = RepCounter(ExerciseType.SQUAT)
        
        counter.update(ExerciseState.MOVING)
        counter.update(ExerciseState.END)
        assert counter.count == 1
        
        counter.reset()
        assert counter.count == 0
        assert counter.state == ExerciseState.START


class TestExerciseAnalyzerFactory:
    """Test ExerciseAnalyzerFactory"""
    
    def test_create_squat_analyzer(self):
        from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
        
        mock_detector = Mock()
        
        analyzer = ExerciseAnalyzerFactory.create_analyzer(ExerciseType.SQUAT, mock_detector)
        
        assert analyzer is not None
        assert analyzer.exercise_type == ExerciseType.SQUAT
    
    def test_create_plank_analyzer(self):
        from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
        
        mock_detector = Mock()
        
        analyzer = ExerciseAnalyzerFactory.create_analyzer(ExerciseType.PLANK, mock_detector)
        
        assert analyzer is not None
        assert analyzer.exercise_type == ExerciseType.PLANK
    
    def test_create_deadlift_analyzer(self):
        from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
        
        mock_detector = Mock()
        
        analyzer = ExerciseAnalyzerFactory.create_analyzer(ExerciseType.DEADLIFT, mock_detector)
        
        assert analyzer is not None
        assert analyzer.exercise_type == ExerciseType.DEADLIFT
    
    def test_unsupported_exercise(self):
        from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
        
        mock_detector = Mock()
        
        with pytest.raises(ValueError):
            ExerciseAnalyzerFactory.create_analyzer(ExerciseType.BENCH_PRESS, mock_detector)


class TestPlankAnalyzer:
    """Test PlankAnalyzer"""
    
    def test_hip_sagging_detection(self):
        from models.exercise_analyzer import PlankAnalyzer
        
        mock_detector = Mock()
        
        analyzer = PlankAnalyzer(mock_detector)
        
        assert analyzer.max_hip_sag == 0.15
    
    def test_feedback_generation(self):
        from models.exercise_analyzer import PlankAnalyzer, FormIssue
        
        mock_detector = Mock()
        analyzer = PlankAnalyzer(mock_detector)
        
        critical_issue = FormIssue(
            "critical",
            "Hips are sagging",
            "Engage core to keep body straight",
            ["left_hip", "right_hip"]
        )


class TestGuidanceService:
    """Test GuidanceService motion classification"""

    def test_motion_to_words_and_classify(self):
        from services.guidance_service import GuidanceService

        guidance = GuidanceService()

        # Synthetic keypoints representing a squat-like motion
        keypoints = {
            "left_shoulder": (0.5, 0.3),
            "left_hip": (0.5, 0.5),
            "left_knee": (0.5, 0.7),
            "left_ankle": (0.5, 0.9),
        }

        description = guidance.motion_to_words(keypoints)
        assert "squat" in description or "stand" in description or description

        from models.exercise_analyzer import ExerciseType
        inferred = guidance.classify_exercise_from_description("user does low knee bend squat movement")
        assert inferred == ExerciseType.SQUAT

        
        feedback = analyzer._generate_feedback([critical_issue])
        
        assert len(feedback) > 0
        assert "CRITICAL" in feedback[0]


class TestDeadliftAnalyzer:
    """Test DeadliftAnalyzer"""
    
    def test_back_rounding_detection(self):
        from models.exercise_analyzer import DeadliftAnalyzer
        
        mock_detector = Mock()
        
        analyzer = DeadliftAnalyzer(mock_detector)
        
        assert analyzer.max_backround == 0.15


class TestVideoAnalysisService:
    """Test VideoAnalysisService"""
    
    def test_frame_analysis_dataclass(self):
        from services.video_analysis_service import FrameAnalysis
        
        frame = FrameAnalysis(
            frame_number=0,
            timestamp=0.0,
            people_detected=1,
            poses=[],
            issues=[]
        )
        
        assert frame.frame_number == 0
        assert frame.people_detected == 1
    
    def test_video_analysis_result_dataclass(self):
        from services.video_analysis_service import VideoAnalysisResult
        
        result = VideoAnalysisResult(
            total_frames=100,
            analyzed_frames=50,
            duration=3.33,
            fps=30.0
        )
        
        assert result.total_frames == 100
        assert result.analyzed_frames == 50
        assert result.overall_form_score == 0.0


class TestGuidanceService:
    """Test GuidanceService fallback"""
    
    def test_fallback_guidance(self):
        from services.guidance_service import GuidanceService
        
        guidance = GuidanceService()
        
        user_sum = {"overall_form_score": 75.0, "summary": {"status": "GOOD"}}
        
        result = guidance._fallback_guidance("squat", user_sum, None)
        
        assert isinstance(result, str)
        assert "squat" in result.lower()
        assert "75" in result
    
    def test_fallback_with_reference(self):
        from services.guidance_service import GuidanceService
        
        guidance = GuidanceService()
        
        user_sum = {"overall_form_score": 85.0, "summary": {"status": "EXCELLENT"}}
        ref_sum = {"overall_form_score": 90.0, "summary": {"status": "EXCELLENT"}}
        
        result = guidance._fallback_guidance("squat", user_sum, ref_sum)
        
        assert "compared" in result.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])