"""
YouTube Video Analysis API Endpoints
Extension to main routes for YouTube video fetching and analysis
"""

from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


def setup_youtube_routes(app):
    """
    Setup YouTube analysis routes
    
    Args:
        app: FastAPI application instance
    """
    from ..services.youtube_service import YouTubeService
    from ..models.exercise_analyzer import ExerciseType
    
    youtube_service = YouTubeService()
    video_analysis_service = None  # Will be set from main routes
    
    @app.post("/api/youtube/video-info")
    async def get_youtube_info(url: str):
        """
        Get information about YouTube video without downloading
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video metadata
        """
        try:
            if not url:
                raise HTTPException(status_code=400, detail="URL is required")
            
            info = await youtube_service.get_video_info(url)
            return info
        
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.post("/api/youtube/analyze")
    async def analyze_youtube_video(
        url: str,
        exercise_type: str = None
    ):
        """
        Fetch YouTube video and analyze exercise form
        
        Args:
            url: YouTube video URL
            exercise_type: Type of exercise to analyze (e.g., 'squat', 'pushup', 'lunge')
            
        Returns:
            Video analysis results with form feedback
        """
        try:
            if not url:
                raise HTTPException(status_code=400, detail="URL is required")
            
            # Check for valid exercise type if provided
            valid_exercises = [e.value for e in ExerciseType]
            if exercise_type and exercise_type.lower() not in valid_exercises:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid exercise type. Valid types: {', '.join(valid_exercises)}"
                )
            
            # Download video
            logger.info(f"Downloading YouTube video: {url}")
            success, video_path, error = await youtube_service.fetch_video(url, max_duration=600)
            
            if not success:
                raise HTTPException(status_code=400, detail=f"Failed to download video: {error}")
            
            try:
                # Extract frames
                logger.info(f"Extracting frames from: {video_path}")
                success, frames, error = await youtube_service.extract_frames(video_path, frame_interval=5)
                
                if not success:
                    raise HTTPException(status_code=400, detail=f"Failed to extract frames: {error}")
                
                if not frames:
                    raise HTTPException(status_code=400, detail="No frames extracted from video")
                
                # Analyze video
                logger.info(f"Analyzing {len(frames)} frames")
                
                # Create progress callback
                async def progress_callback(data):
                    logger.info(f"Progress: {data['progress']:.1f}% - Frame {data['current_frame']}/{data['total_frames']}")
                
                from ..services.video_analysis_service import VideoAnalysisService
                from ..models.pose_estimator import MediaPipePoseDetector
                from ..models.exercise_analyzer import ExerciseAnalyzerFactory
                
                pose_detector = MediaPipePoseDetector()
                analyzer = ExerciseAnalyzerFactory.create_analyzer(ExerciseType.SQUAT, pose_detector)
                video_analysis_service = VideoAnalysisService(pose_detector, analyzer)
                
                analysis_result = await video_analysis_service.analyze_frames(
                    frames=frames,
                    exercise_type=exercise_type,
                    callback=progress_callback
                )
                
                # Convert to dictionary for JSON response
                return {
                    "success": True,
                    "url": url,
                    "exercise_type": exercise_type or "general",
                    "total_frames": analysis_result.total_frames,
                    "analyzed_frames": analysis_result.analyzed_frames,
                    "duration": round(analysis_result.duration, 2),
                    "fps": analysis_result.fps,
                    "summary": analysis_result.summary,
                    "frame_analyses": analysis_result.frame_analyses[:20]  # Return first 20 frames for detail
                }
            
            finally:
                # Clean up downloaded video
                logger.info(f"Cleaning up video file: {video_path}")
                youtube_service.cleanup_video(video_path)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error analyzing YouTube video: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


    @app.get("/api/youtube/supported-exercises")
    async def get_supported_exercises():
        """
        Get list of supported exercise types for analysis
        
        Returns:
            List of supported exercises
        """
        try:
            exercises = [
                {
                    "type": exercise.value,
                    "name": exercise.value.replace("_", " ").title(),
                    "description": get_exercise_description(exercise.value)
                }
                for exercise in ExerciseType
            ]
            
            return {
                "success": True,
                "exercises": exercises,
                "total": len(exercises)
            }
        
        except Exception as e:
            logger.error(f"Error getting supported exercises: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


def get_exercise_description(exercise_type: str) -> str:
    """Get description for exercise type"""
    descriptions = {
        "squat": "Lower body exercise - form check for knee alignment and depth",
        "pushup": "Upper body exercise - form check for body alignment and elbow position",
        "lunge": "Lower body exercise - form check for knee and hip alignment",
        "plank": "Core exercise - form check for body alignment and hip position",
        "deadlift": "Lower body compound - form check for back alignment and lift mechanics",
        "bench_press": "Upper body compound - form check for bar path and elbow position",
        "overhead_press": "Upper body exercise - form check for core engagement and shoulder stability",
        "bicep_curl": "Upper body isolation - form check for elbow position and arm movement",
        "tricep_extension": "Upper body isolation - form check for arm alignment and range of motion",
        "jumping_jack": "Cardio exercise - form check for coordination and body alignment"
    }
    return descriptions.get(exercise_type, "Exercise form analysis")
