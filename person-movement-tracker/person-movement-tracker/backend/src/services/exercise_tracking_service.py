"""
Exercise Tracking Service
Handles exercise form analysis and feedback generation
"""

import time
import base64
import numpy as np
import cv2
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

try:
    from ..models.pose_estimator import MediaPipePoseDetector, PoseLandmarks
    from ..models.exercise_analyzer import (
        ExerciseAnalyzerFactory, ExerciseType, ExerciseAnalyzer
    )
    from ..utils.image_processor import ImageProcessor
except ImportError:
    from models.pose_estimator import MediaPipePoseDetector, PoseLandmarks
    from models.exercise_analyzer import (
        ExerciseAnalyzerFactory, ExerciseType, ExerciseAnalyzer
    )
    from utils.image_processor import ImageProcessor


class ExerciseTrackingService:
    """Service for exercise form tracking and analysis"""
    
    def __init__(self):
        self.pose_detector: Optional[MediaPipePoseDetector] = None
        self.analyzers: Dict[ExerciseType, ExerciseAnalyzer] = {}
        self.image_processor = ImageProcessor()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the pose detector and analyzers"""
        if self._initialized:
            return
        
        try:
            # Initialize pose detector
            self.pose_detector = MediaPipePoseDetector(
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                device="cpu"
            )
            
            # Initialize analyzers for supported exercises
            supported_exercises = [
                ExerciseType.SQUAT,
                ExerciseType.PUSHUP,
                ExerciseType.LUNGE
            ]
            
            for exercise_type in supported_exercises:
                try:
                    analyzer = ExerciseAnalyzerFactory.create_analyzer(
                        exercise_type, self.pose_detector
                    )
                    self.analyzers[exercise_type] = analyzer
                except Exception as e:
                    print(f"Failed to initialize analyzer for {exercise_type}: {e}")
            
            self._initialized = True
            print("Exercise tracking service initialized successfully")
        
        except Exception as e:
            print(f"Failed to initialize exercise tracking service: {e}")
            raise
    
    async def process_frame(
        self,
        image_data: str,
        session_id: str,
        exercise_type: ExerciseType,
        enable_tracking: bool = True
    ) -> Dict[str, Any]:
        """
        Process a frame for exercise form analysis
        
        Args:
            image_data: Base64 encoded image
            session_id: Session identifier
            exercise_type: Type of exercise to analyze
            enable_tracking: Whether to enable tracking
            
        Returns:
            Analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Decode image
            frame = self.image_processor.decode_base64(image_data)
            
            if frame is None:
                return {
                    'success': False,
                    'error': 'Failed to decode image'
                }
            
            # Get analyzer for exercise type
            analyzer = self.analyzers.get(exercise_type)
            if not analyzer:
                return {
                    'success': False,
                    'error': f'Unsupported exercise type: {exercise_type}'
                }
            
            # Detect pose
            poses = self.pose_detector.detect(frame)
            
            if not poses:
                return {
                    'success': True,
                    'pose_data': None,
                    'analysis': None,
                    'inference_time': time.time() - start_time
                }
            
            # Get the first pose (assuming single person)
            pose = poses[0]
            
            # Analyze form
            analysis = analyzer.analyze(pose, frame)
            
            # Draw landmarks on frame
            frame_with_landmarks = self.pose_detector.draw_landmarks(frame, pose)
            
            # Encode frame
            encoded_image = self.image_processor.encode_base64(frame_with_landmarks)
            
            # Prepare pose data
            pose_data = {
                'landmarks': pose.landmarks,
                'confidence': pose.confidence,
                'timestamp': pose.timestamp
            }
            
            return {
                'success': True,
                'image': encoded_image,
                'pose_data': pose_data,
                'analysis': analysis,
                'inference_time': time.time() - start_time
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'inference_time': time.time() - start_time
            }
    
    def reset_analyzer(self, exercise_type: ExerciseType) -> None:
        """Reset the analyzer for a specific exercise"""
        analyzer = self.analyzers.get(exercise_type)
        if analyzer:
            analyzer.reset()
    
    def get_supported_exercises(self) -> list:
        """Get list of supported exercise types"""
        return list(self.analyzers.keys())
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.pose_detector:
            self.pose_detector.cleanup()
        self.executor.shutdown(wait=True)
        self._initialized = False
