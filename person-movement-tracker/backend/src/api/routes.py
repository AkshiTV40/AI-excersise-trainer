from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
import os
import tempfile
import time
from uuid import uuid4
import numpy as np
import cv2
from ..database import init_db, get_db_connection, add_video, get_video, get_videos, delete_video, update_video_analysis
from ..api.schemas import Video, VideoCreate, VideoList
from ..utils.video_processor import VideoStream
from pathlib import Path

logger = logging.getLogger(__name__)

# Recordings directory
RECORDINGS_DIR = Path(__file__).parent.parent.parent / "data" / "videos" / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

try:
    from ..config import config
    from ..services.tracking_service import TrackingService
    from ..services.youtube_service import YouTubeService
    from ..services.video_analysis_service import VideoAnalysisService
    from ..models.detector_factory import ModelType
    from ..models.pose_estimator import MediaPipePoseDetector
    from ..models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
    from .schemas import (
        TrackingRequest, TrackingResponse, ModelInfo,
        DeviceInfo, SessionStats, ExerciseTrackingRequest,
        ExerciseTrackingResponse
    )
except ImportError:
    from config import config
    from services.tracking_service import TrackingService
    from services.youtube_service import YouTubeService
    from services.video_analysis_service import VideoAnalysisService
    from models.detector_factory import ModelType
    from models.pose_estimator import MediaPipePoseDetector
    from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
    from api.schemas import (
        TrackingRequest, TrackingResponse, ModelInfo,
        DeviceInfo, SessionStats, ExerciseTrackingRequest,
        ExerciseTrackingResponse
    )

app = FastAPI(
    title="Person Movement Tracker API",
    description="Real-time person detection and tracking API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
tracking_service = TrackingService()
exercise_tracking_service = None
youtube_service = YouTubeService()
video_analysis_service = None
guidance_service = None
background_form_detector = None
exercise_form_tracker = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    init_db()
    await tracking_service.initialize()
    global exercise_tracking_service, video_analysis_service, background_form_detector, guidance_service
    from ..services.exercise_tracking_service import ExerciseTrackingService

    exercise_tracking_service = ExerciseTrackingService()
    await exercise_tracking_service.initialize()

    # Initialize video analysis service with default SQUAT analyzer
    pose_detector = MediaPipePoseDetector()
    analyzer = ExerciseAnalyzerFactory.create_analyzer(ExerciseType.SQUAT, pose_detector)
    video_analysis_service = VideoAnalysisService(pose_detector, analyzer)

    # Initialize background form detector with YOLO pose and classifier
    try:
        from ..services.background_form_detector import BackgroundFormDetector
        classifier_model = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "decision_tree_form_model.pkl")
        background_form_detector = BackgroundFormDetector(
            yolo_model="yolov8n-pose.pt",
            classifier_model=classifier_model if os.path.exists(classifier_model) else None,
            device="cpu"
        )
    except Exception as e:
        logger.warning(f"Could not initialize BackgroundFormDetector: {e}")
        background_form_detector = None

    # Optional AI guidance using Qwen transformer model
    try:
        from ..services.guidance_service import GuidanceService
        guidance_service = GuidanceService()
    except Exception as e:
        logger.warning(f"Could not initialize GuidanceService: {e}")
        guidance_service = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """API root with documentation"""
    return """
    <html>
        <head>
            <title>Person Movement Tracker API</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>Person Movement Tracker API</h1>
            <p>Real-time person detection and tracking service</p>
            <div class="endpoint">
                <h3>POST /api/track</h3>
                <p>Process frame with person detection and tracking</p>
            </div>
            <div class="endpoint">
                <h3>WS /ws/track</h3>
                <p>WebSocket for real-time tracking</p>
            </div>
            <div class="endpoint">
                <h3>GET /api/models</h3>
                <p>Get available models</p>
            </div>
        </body>
    </html>
    """


@app.post("/api/track", response_model=TrackingResponse)
async def track_persons(request: TrackingRequest):
    """Process image/video frame for person tracking"""
    result = await tracking_service.process_frame(
        image_data=request.image,
        session_id=request.session_id,
        model_type=request.model_type,
        enable_tracking=request.enable_tracking
    )

    if result['success']:
        return TrackingResponse(
            success=True,
            image=result['image'],
            detections=result['detections'],
            inference_time=result['inference_time'],
            track_count=result['track_count'],
            model=result['model']
        )
    else:
        return TrackingResponse(
            success=False,
            error=result['error']
        )


@app.post("/api/track/file")
async def track_from_file(
        file: UploadFile = File(...),
        model_type: Optional[str] = Form("yolov8"),
        enable_tracking: bool = Form(True)
):
    """Upload image file for tracking"""
    try:
        # Read file
        contents = await file.read()

        # Convert to base64
        import base64
        image_data = base64.b64encode(contents).decode('utf-8')

        # Process
        result = await tracking_service.process_frame(
            image_data=image_data,
            session_id="file_upload",
            model_type=ModelType(model_type) if model_type else None,
            enable_tracking=enable_tracking
        )

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )


@app.get("/api/models", response_model=List[ModelInfo])
async def get_models():
    """Get available models"""
    from ..models.detector_factory import DetectorFactory

    models = DetectorFactory.get_available_models()

    return [
        ModelInfo(
            name=model_type.value,
            description=info['description'],
            supports_tracking=info['supports_tracking']
        )
        for model_type, info in models.items()
    ]


@app.get("/api/device", response_model=DeviceInfo)
async def get_device_info():
    """Get device information and capabilities"""
    import torch

    device_info = {
        'device': str(config.device),
        'cuda_available': torch.cuda.is_available(),
        'mps_available': hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
        'cpu_count': torch.get_num_threads()
    }

    if torch.cuda.is_available():
        device_info['cuda_device_count'] = torch.cuda.device_count()
        device_info['cuda_device_name'] = torch.cuda.get_device_name(0)

    return DeviceInfo(**device_info)


@app.post("/api/guidance/motion-to-exercise")
async def guidance_motion_to_exercise(payload: Dict[str, Any]):
    """Convert motion keypoints into words, infer exercise, and provide analysis guidance."""
    global guidance_service
    if guidance_service is None:
        try:
            from ..services.guidance_service import GuidanceService
            guidance_service = GuidanceService()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Guidance service unavailable: {str(e)}")

    keypoints = payload.get("keypoints") or payload.get("pose_keypoints")
    additional_context = payload.get("context")

    if not keypoints:
        raise HTTPException(status_code=400, detail="Missing 'keypoints' in request body")

    motion_description = guidance_service.motion_to_words(keypoints, additional_context)
    exercise_type = guidance_service.classify_exercise_from_description(motion_description)
    matched = exercise_type.value if exercise_type else "unknown"
    result = guidance_service.remote_exercise_match(motion_description)

    return {
        "motion_description": motion_description,
        "inferred_exercise": matched,
        "suggested_query": result.get("suggested_query"),
        "analysis": result.get("analysis"),
        "token_type": guidance_service.get_token_guidance()
    }


@app.websocket("/ws/track")
async def websocket_track(websocket: WebSocket):
    """WebSocket for real-time tracking"""
    await websocket.accept()

    session_id = f"ws_{websocket.client.host}"

    try:
        while True:
            # Receive frame
            data = await websocket.receive_json()
            image_data = data.get('image')

            if not image_data:
                continue

            # Process frame
            result = await tracking_service.process_frame(
                image_data=image_data,
                session_id=session_id,
                enable_tracking=True
            )

            # Send result
            await websocket.send_json(result)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        await websocket.send_json({'error': str(e)})


@app.get("/api/session/{session_id}/stats", response_model=SessionStats)
async def get_session_stats(session_id: str):
    """Get session statistics"""
    # This would typically come from a database
    return SessionStats(
        session_id=session_id,
        frame_count=100,
        average_inference_time=0.15,
        total_tracks=5
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "person-tracker"}


# Exercise Tracking Endpoints

@app.post("/api/exercise/track", response_model=ExerciseTrackingResponse)
async def track_exercise(request: ExerciseTrackingRequest):
    """Process frame for exercise form analysis"""
    if not exercise_tracking_service:
        return ExerciseTrackingResponse(
            success=False,
            error="Exercise tracking service not initialized"
        )

    result = await exercise_tracking_service.process_frame(
        image_data=request.image,
        session_id=request.session_id,
        exercise_type=request.exercise_type,
        enable_tracking=request.enable_tracking
    )

    if result['success']:
        return ExerciseTrackingResponse(
            success=True,
            image=result.get('image'),
            pose_data=result.get('pose_data'),
            analysis=result.get('analysis'),
            inference_time=result['inference_time']
        )
    else:
        return ExerciseTrackingResponse(
            success=False,
            error=result.get('error')
        )


@app.post("/api/exercise/track/file")
async def track_exercise_from_file(
        file: UploadFile = File(...),
        exercise_type: str = Form("squat"),
        enable_tracking: bool = Form(True)
):
    """Upload image file for exercise tracking"""
    if not exercise_tracking_service:
        return JSONResponse(
            status_code=500,
            content={'error': 'Exercise tracking service not initialized'}
        )

    try:
        # Read file
        contents = await file.read()

        # Convert to base64
        import base64
        image_data = base64.b64encode(contents).decode('utf-8')

        # Process
        result = await exercise_tracking_service.process_frame(
            image_data=image_data,
            session_id="file_upload",
            exercise_type=ExerciseType(exercise_type),
            enable_tracking=enable_tracking
        )

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )


@app.post("/api/exercise/track/video")
async def track_exercise_video(
        file: UploadFile = File(...),
        exercise_type: str = Form("squat"),
        reference_url: Optional[str] = Form(None),
        max_seconds: int = Form(10)
):
    """Upload a 5-10 second video and run exercise form analysis plus comparison feedback"""
    if not video_analysis_service:
        return JSONResponse(status_code=500, content={'error': 'Video analysis service not initialized'})

    temp_path = os.path.join(tempfile.gettempdir(), f"exercise_upload_{int(time.time() * 1000)}.mp4")

    try:
        # Save upload to disk
        contents = await file.read()
        with open(temp_path, 'wb') as out_file:
            out_file.write(contents)

        # Analyze the uploaded clip
        user_result = await video_analysis_service.analyze_video_file(
            video_path=temp_path,
            exercise_type=exercise_type,
            max_seconds=max_seconds,
            sample_rate=2.0
        )

        reference_analysis = None
        if reference_url:
            fetch_success, ref_path, fetch_error = await youtube_service.fetch_video(reference_url, max_duration=120)
            if fetch_success and ref_path:
                try:
                    reference_analysis = await video_analysis_service.analyze_video_file(
                        video_path=ref_path,
                        exercise_type=exercise_type,
                        max_seconds=max_seconds,
                        sample_rate=2.0
                    )
                finally:
                    youtube_service.cleanup_video(ref_path)
            else:
                logger.warning(f"Unable to fetch reference video: {fetch_error}")

        training_links = {
            'squat': ['https://www.youtube.com/watch?v=aclHkVaku9U', 'https://www.youtube.com/watch?v=Dy28eq2PjcM'],
            'pushup': ['https://www.youtube.com/watch?v=IODxDxX7oi4', 'https://www.youtube.com/watch?v=_l3ySVKYVJ8'],
            'lunge': ['https://www.youtube.com/watch?v=QOVaHwm-Q6U'],
            'plank': ['https://www.youtube.com/watch?v=pSHjTRCQxIw']
        }

        user_summary_for_guidance = {
            'overall_form_score': user_result.overall_form_score,
            'summary': user_result.summary,
            'form_issues': [
                issue for frame in user_result.frame_analyses[-20:] for issue in frame.get('issues', [])
            ]
        }

        ai_summary = guidance_service.generate_guidance(
            exercise_type=exercise_type,
            user_summary=user_summary_for_guidance,
            reference_summary={
                'overall_form_score': reference_analysis.overall_form_score,
                'summary': reference_analysis.summary
            } if reference_analysis else None
        ) if guidance_service else 'Guidance service is unavailable on the server.'

        comparison = None
        if reference_analysis:
            comparison = {
                'user_score': round(user_result.overall_form_score, 1),
                'reference_score': round(reference_analysis.overall_form_score, 1),
                'score_gap': round(user_result.overall_form_score - reference_analysis.overall_form_score, 1)
            }

        return {
            'success': True,
            'exercise_type': exercise_type,
            'total_frames': user_result.total_frames,
            'analyzed_frames': user_result.analyzed_frames,
            'user_analysis': user_result.summary,
            'user_form_score': round(user_result.overall_form_score, 1),
            'reference_analysis': reference_analysis.summary if reference_analysis else None,
            'comparison': comparison,
            'reference_tutorials': training_links.get(exercise_type.lower(), []),
            'ai_guidance': ai_summary
        }

    except Exception as e:
        logger.error(f"Error in track_exercise_video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/api/exercise/types")
async def get_exercise_types():
    """Get supported exercise types"""
    if not exercise_tracking_service:
        return {"exercises": []}

    exercises = exercise_tracking_service.get_supported_exercises()

    return {
        "exercises": [
            {
                "type": ex.value,
                "name": ex.value.replace("_", " ").title()
            }
            for ex in exercises
        ]
    }


@app.post("/api/exercise/reset")
async def reset_exercise_tracking(exercise_type: str):
    """Reset exercise tracking for a specific exercise"""
    if not exercise_tracking_service:
        return {"success": False, "error": "Service not initialized"}

    try:
        ex_type = ExerciseType(exercise_type)
        exercise_tracking_service.reset_analyzer(ex_type)
        return {"success": True, "message": f"Reset tracking for {exercise_type}"}
    except ValueError:
        return {"success": False, "error": f"Invalid exercise type: {exercise_type}"}


@app.get("/api/videos/{video_id}")
async def get_video_file(video_id: int):
    """Serve video file by ID"""
    video_record = get_video(video_id)
    if not video_record:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = _video_record_path(video_record)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        path=video_path,
        media_type='video/mp4',
        filename=video_record['original_filename']
    )


@app.delete("/api/videos/{video_id}")
async def delete_video_file(video_id: int):
    """Delete a video metadata row and its MP4 file."""
    init_db()
    video_record = get_video(video_id)
    if not video_record:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = _video_record_path(video_record)
    if video_path.exists():
        try:
            os.remove(video_path)
        except OSError as exc:
            logger.exception("Failed to delete video file %s", video_path)
            raise HTTPException(status_code=500, detail=f"Failed to delete video file: {exc}")

    deleted = delete_video(video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Video not found")

    return {"success": True, "video_id": video_id, "deleted_file": str(video_path)}


# Background Form Detection Endpoints

@app.post("/api/background/analyze")
async def analyze_background_form(
        file: UploadFile = File(...),
        exercise_type: str = Form("squat"),
        skip_frames: int = Form(3)
):
    """Upload video for background form analysis using YOLO + XGBoost classifier"""
    if not background_form_detector:
        return JSONResponse(
            status_code=500,
            content={'error': 'Background form detector not initialized'}
        )

    import base64
    import cv2

    temp_path = os.path.join(tempfile.gettempdir(), f"background_analyze_{int(time.time() * 1000)}.mp4")

    try:
        # Save upload to disk
        contents = await file.read()
        with open(temp_path, 'wb') as out_file:
            out_file.write(contents)

        # Extract frames from video
        cap = cv2.VideoCapture(temp_path)
        frames = []

        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % skip_frames == 0:
                frame_resized = cv2.resize(frame, (640, 480))
                frames.append(frame_resized)

            frame_idx += 1

        cap.release()

        if not frames:
            return JSONResponse(
                status_code=400,
                content={'error': 'No frames extracted from video'}
            )

        # Analyze frames
        analysis_results = background_form_detector.analyze_video_frames(frames, skip_frames=1)

        # Get aggregate analysis
        aggregate = background_form_detector.get_aggregate_analysis(analysis_results)

        # Get sample keypoints and angles from first valid result
        sample_keypoints = {}
        sample_angles = {}

        for result in analysis_results:
            if result.keypoints:
                sample_keypoints = {k: list(v) for k, v in result.keypoints.items()}
                sample_angles = result.angles
                break

        return {
            'success': True,
            'exercise_type': exercise_type,
            'frames_analyzed': len(frames),
            'aggregate_analysis': aggregate,
            'sample_keypoints': sample_keypoints,
            'sample_angles': sample_angles
        }

    except Exception as e:
        logger.error(f"Error in background form analysis: {e}")
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/api/background/analyze/frame")
async def analyze_single_frame_background(
        image: UploadFile = File(...),
        exercise_type: str = Form("squat")
):
    """Analyze a single image frame for background form detection"""
    if not background_form_detector:
        return JSONResponse(
            status_code=500,
            content={'error': 'Background form detector not initialized'}
        )

    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return JSONResponse(
                status_code=400,
                content={'error': 'Could not decode image'}
            )

        frame_resized = cv2.resize(frame, (640, 480))
        result = background_form_detector.analyze_frame(frame_resized, frame_idx=0)

        keypoints_dict = {}
        if result.keypoints:
            keypoints_dict = {k: list(v) for k, v in result.keypoints.items()}

        return {
            'success': True,
            'exercise_type': exercise_type,
            'keypoints': keypoints_dict,
            'angles': result.angles,
            'form_classification': {
                'label': result.form_classification.form_label if result.form_classification else None,
                'confidence': result.form_classification.confidence if result.form_classification else 0.0,
                'is_good_form': result.form_classification.is_good_form if result.form_classification else None
            } if result.form_classification else None
        }

    except Exception as e:
        logger.error(f"Error in single frame analysis: {e}")
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )


@app.post("/api/guidance/test")
async def test_guidance(
        exercise_type: str = Form("squat"),
        form_score: float = Form(72.0)
):
    """Test Qwen guidance generation and token configuration."""
    global guidance_service
    if not guidance_service:
        try:
            from ..services.guidance_service import GuidanceService
            guidance_service = GuidanceService()
        except Exception as e:
            return {
                "success": False,
                "ready": False,
                "error": str(e)
            }

    try:
        guidance = guidance_service.generate_guidance(
            exercise_type=exercise_type,
            user_summary={
                "overall_form_score": form_score,
                "summary": {
                    "status": "NEEDS IMPROVEMENT",
                    "frames_with_people": 18,
                    "total_frames": 20,
                    "critical_issues": 0,
                    "warnings": 4,
                    "info_messages": 2,
                    "exercise_type": exercise_type,
                    "recommendations": ["Review technique before increasing volume"]
                },
                "form_issues": [
                    {
                        "severity": "warning",
                        "message": "Knee tracking was inconsistent",
                        "suggestion": "Keep knees aligned with toes"
                    }
                ]
            }
        )
        return {
            "success": True,
            "ready": guidance_service.is_ready,
            "model": guidance_service.model_name,
            "guidance": guidance
        }
    except Exception as e:
        logger.warning(f"Guidance test failed: {e}")
        return {
            "success": False,
            "ready": guidance_service.is_ready if guidance_service else False,
            "model": guidance_service.model_name if guidance_service else None,
            "error": str(e)
        }


@app.get("/api/background/status")
async def get_background_detector_status():
    """Get background form detector status"""
    if not background_form_detector:
        return {
            'status': 'not_initialized',
            'message': 'Background form detector not available'
        }

    return {
        'status': 'ready',
        'model': 'yolov8n-pose',
        'classifier': 'decision_tree' if background_form_detector.classifier and background_form_detector.classifier.is_trained else 'heuristic'
    }


@app.websocket("/ws/exercise/track")
async def websocket_exercise_track(websocket: WebSocket):
    """WebSocket for real-time exercise tracking"""
    await websocket.accept()

    session_id = f"ws_exercise_{websocket.client.host}"
    current_exercise_type = None

    try:
        while True:
            # Receive frame
            data = await websocket.receive_json()
            image_data = data.get('image')
            exercise_type_str = data.get('exercise_type', 'squat')

            if not image_data:
                continue

            # Reset if exercise type changed
            if current_exercise_type != exercise_type_str:
                current_exercise_type = exercise_type_str
                try:
                    exercise_tracking_service.reset_analyzer(ExerciseType(exercise_type_str))
                except ValueError:
                    pass

            # Process frame
            result = await exercise_tracking_service.process_frame(
                image_data=image_data,
                session_id=session_id,
                exercise_type=ExerciseType(exercise_type_str),
                enable_tracking=True
            )

            # Send result
            await websocket.send_json(result)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        await websocket.send_json({'error': str(e)})


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _json_dumps(value: Any) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False)


def _video_record_path(video_record: Dict[str, Any]) -> Path:
    return RECORDINGS_DIR / video_record['filename']


def _safe_filename_part(value: Any) -> str:
    text = str(value or 'unknown')
    return ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in text)


def _parse_reference_video_id(value: Any) -> Optional[int]:
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid reference_video_id: {value}")


def _validate_recording_config(exercise_type_value: Any, duration_value: Any) -> tuple[str, int]:
    try:
        exercise_type = ExerciseType(exercise_type_value).value
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid exercise type: {exercise_type_value}. Valid types are: {[e.value for e in ExerciseType]}")

    try:
        duration_seconds = int(float(duration_value))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="duration_seconds must be a number")

    duration_seconds = max(1, min(duration_seconds, 120))
    return exercise_type, duration_seconds


def _resolve_video_input(video_input: Any) -> Path:
    video_id = _parse_reference_video_id(video_input)
    if video_id is not None:
        video_record = get_video(video_id)
        if not video_record:
            raise HTTPException(status_code=404, detail=f"Video not found: {video_input}")
        return _video_record_path(video_record)

    video_path = Path(str(video_input))
    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Video file not found: {video_input}")
    return video_path


def _write_frames_to_video(frames: List[np.ndarray], video_path: Path, fps: float) -> tuple:
    height, width = frames[0].shape[:2]
    writer_fps = max(float(fps or 10.0), 1.0)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, writer_fps, (width, height))

    if not out.isOpened():
        raise RuntimeError(f"Failed to open VideoWriter for {video_path}")

    try:
        for frame in frames:
            out.write(frame)
    finally:
        out.release()

    if not video_path.exists() or video_path.stat().st_size == 0:
        raise RuntimeError(f"Video file was not created at {video_path}")

    return width, height, writer_fps


def _analysis_to_dict(analysis_result: Any) -> Optional[Dict[str, Any]]:
    if analysis_result is None:
        return None

    return {
        "total_frames": int(analysis_result.total_frames),
        "analyzed_frames": int(analysis_result.analyzed_frames),
        "duration": float(analysis_result.duration),
        "fps": float(analysis_result.fps),
        "detected_exercise": analysis_result.detected_exercise,
        "overall_form_score": float(analysis_result.overall_form_score),
        "summary": _json_safe(analysis_result.summary),
        "frame_analyses": _json_safe(analysis_result.frame_analyses),
    }


def _feedback_from_analysis(analysis_result: Any, exercise_type: str) -> str:
    if analysis_result is None:
        return "Video saved, but analysis service was not available."

    if guidance_service and guidance_service.is_ready:
        user_summary = {
            "overall_form_score": float(analysis_result.overall_form_score),
            "summary": analysis_result.summary,
            "form_issues": [
                issue for frame in analysis_result.frame_analyses for issue in frame.get('issues', [])
            ]
        }
        return guidance_service.generate_guidance(
            exercise_type=exercise_type,
            user_summary=user_summary,
            reference_summary=None
        )

    score = float(analysis_result.overall_form_score)
    if score >= 85:
        verdict = "excellent"
    elif score >= 70:
        verdict = "good"
    elif score >= 50:
        verdict = "needs improvement"
    else:
        verdict = "needs major correction"

    summary = analysis_result.summary or {}
    return (
        f"Overall Summary: Your {exercise_type} form was {verdict} "
        f"with an average score of {score:.1f}% across "
        f"{analysis_result.analyzed_frames}/{analysis_result.total_frames} analyzed frames.\n\n"
        f"Summary: {summary.get('status', 'N/A')}\n\n"
        f"Recommendations: {', '.join(summary.get('recommendations', []))}"
    )


def _get_exercise_form_tracker():
    global exercise_form_tracker
    if exercise_form_tracker is None:
        from ..services.exercise_form_tracker import ExerciseFormTracker
        exercise_form_tracker = ExerciseFormTracker(device=str(config.device))
    return exercise_form_tracker


# Helper function to process recorded video (used in WebSocket)
async def _process_recorded_video(
        frames: List[np.ndarray],
        session_id: str,
        exercise_type: str,
        start_time: float,
        fps: float,
        duration_seconds: Optional[float] = None,
        reference_video_id: Optional[int] = None,
        reference_video_path: Optional[str] = None
) -> Dict[str, Any]:
    """Save live video to disk, store metadata in SQLite3, analyze, and optionally compare."""
    init_db()
    if not frames:
        raise RuntimeError("No frames recorded")

    reference_video_id = _parse_reference_video_id(reference_video_id)
    timestamp = int(start_time or time.time())
    filename = f"session_{_safe_filename_part(session_id)}_{_safe_filename_part(exercise_type)}_{timestamp}_{uuid4().hex[:8]}.mp4"
    video_path = RECORDINGS_DIR / filename

    elapsed_time = max(time.time() - start_time, 0.001) if start_time else 0.001
    actual_fps = len(frames) / elapsed_time if elapsed_time > 0 else fps
    width, height, writer_fps = _write_frames_to_video(frames, video_path, actual_fps)
    duration = len(frames) / writer_fps if writer_fps > 0 else elapsed_time

    video_id = add_video(
        filename=filename,
        original_filename=f"exercise_session_{exercise_type}_{timestamp}.mp4",
        exercise_type=exercise_type,
        file_size=video_path.stat().st_size,
        duration=duration,
        width=width,
        height=height,
        description=f"Live recorded session for {exercise_type}",
        source="live",
        session_id=session_id,
        analysis_status="processing",
        reference_video_id=reference_video_id
    )

    analysis_result = None
    analysis_payload = None
    feedback_text = "Video saved, but analysis service was not available."
    analysis_error = None

    if video_analysis_service:
        try:
            analysis_result = await video_analysis_service.analyze_video_file(
                video_path=str(video_path),
                exercise_type=exercise_type,
                max_seconds=max(1, int(duration_seconds or duration or 30)),
                sample_rate=2.0
            )
            analysis_payload = _analysis_to_dict(analysis_result)
            feedback_text = _feedback_from_analysis(analysis_result, exercise_type)
        except Exception as e:
            logger.exception("Error analyzing recorded live session")
            analysis_error = str(e)
            feedback_text = f"Video saved, but analysis failed: {e}"
    else:
        analysis_error = "Video analysis service is not initialized"

    comparison_report = None
    comparison_error = None
    if reference_video_id or reference_video_path:
        try:
            tracker = _get_exercise_form_tracker()
            reference_path = None
            parsed_reference_video_id = _parse_reference_video_id(reference_video_id)
            if parsed_reference_video_id:
                reference_record = get_video(parsed_reference_video_id)
                if not reference_record:
                    comparison_error = f"Reference video not found: {parsed_reference_video_id}"
                else:
                    reference_path = str(_video_record_path(reference_record))
            elif reference_video_path:
                resolved_reference_path = Path(reference_video_path)
                if not resolved_reference_path.exists():
                    comparison_error = f"Reference video file not found: {reference_video_path}"
                else:
                    reference_path = str(resolved_reference_path)

            if reference_path and comparison_error is None:
                comparison_report = tracker.compare_videos(
                    reference_video_path=reference_path,
                    user_video_path=str(video_path),
                    max_frames=120,
                    sample_rate_hz=2.0,
                    motion_select=True,
                    motion_top_k=60,
                    upscale=(640, 480)
                )
        except Exception as e:
            logger.exception("Error comparing recorded live session")
            comparison_error = str(e)

    analysis_document = {
        "analysis": analysis_payload,
        "comparison": comparison_report,
        "feedback": feedback_text,
        "video_id": video_id,
        "source": "live",
        "session_id": session_id,
        "analysis_error": analysis_error,
        "comparison_error": comparison_error,
    }
    update_video_analysis(
        video_id,
        "completed" if analysis_error is None else "failed",
        _json_dumps(analysis_document)
    )

    return {
        "video_id": video_id,
        "video_url": f"/api/videos/{video_id}",
        "exercise_type": exercise_type,
        "duration": round(duration, 3),
        "duration_seconds": round(duration, 3),
        "frames_processed": len(frames),
        "actual_fps": round(writer_fps, 3),
        "width": width,
        "height": height,
        "source": "live",
        "session_id": session_id,
        "analysis": analysis_payload or {"overall_form_score": None, "summary": {}},
        "comparison": comparison_report,
        "feedback": feedback_text,
        "analysis_status": "completed" if analysis_error is None else "failed",
    }


@app.post("/api/exercise/compare")
async def compare_form_videos(payload: Dict[str, Any]):
    """Compare two saved videos or local video paths using the form tracker."""
    reference_input = payload.get("reference_video") or payload.get("reference_video_id")
    user_input = payload.get("user_video") or payload.get("user_video_id")
    exercise_type = payload.get("exercise_type", "squat")

    if not reference_input or not user_input:
        raise HTTPException(status_code=400, detail="Missing reference_video and user_video")

    tracker = _get_exercise_form_tracker()
    reference_path = _resolve_video_input(reference_input)
    user_path = _resolve_video_input(user_input)

    report = tracker.compare_videos(
        reference_video_path=str(reference_path),
        user_video_path=str(user_path),
        max_frames=int(payload.get("max_frames", 120)),
        sample_rate_hz=float(payload.get("sample_rate_hz", 2.0)),
        motion_select=bool(payload.get("motion_select", True)),
        motion_top_k=int(payload.get("motion_top_k", 60)),
        upscale=tuple(payload["upscale"]) if payload.get("upscale") else (640, 480),
        save_overlays=bool(payload.get("save_overlays", False)),
        overlays_dir=payload.get("overlays_dir")
    )

    return {
        "success": True,
        "reference_video": str(reference_path),
        "user_video": str(user_path),
        "exercise_type": exercise_type,
        "report": _json_safe(report)
    }


@app.post("/api/exercise/compare/video-ids")
async def compare_saved_videos(
        reference_video_id: int = Form(...),
        user_video_id: int = Form(...),
        exercise_type: str = Form("squat"),
        max_frames: int = Form(120),
        sample_rate_hz: float = Form(2.0)
):
    """Compare two videos already saved in SQLite3."""
    reference_record = get_video(reference_video_id)
    user_record = get_video(user_video_id)

    if not reference_record:
        raise HTTPException(status_code=404, detail=f"Reference video not found: {reference_video_id}")
    if not user_record:
        raise HTTPException(status_code=404, detail=f"User video not found: {user_video_id}")

    tracker = _get_exercise_form_tracker()
    report = tracker.compare_videos(
        reference_video_path=str(_video_record_path(reference_record)),
        user_video_path=str(_video_record_path(user_record)),
        max_frames=max_frames,
        sample_rate_hz=sample_rate_hz,
        motion_select=True,
        motion_top_k=min(60, max_frames),
        upscale=(640, 480)
    )

    return {
        "success": True,
        "reference_video_id": reference_video_id,
        "user_video_id": user_video_id,
        "exercise_type": exercise_type,
        "report": _json_safe(report)
    }


@app.websocket("/ws/record-session")
async def websocket_record_session(websocket: WebSocket):
    """WebSocket for recording exercise sessions and providing feedback"""
    await websocket.accept()

    session_id = f"ws_record_{_safe_filename_part(websocket.client.host)}"

    # Recording state
    is_recording = False
    # YOLO-based offline analyzer (video-based compare)
    # NOTE: Live overlay currently uses YOLO pose; analysis uses VideoAnalysisService.

    frames = []
    start_time = None
    exercise_type = "squat"  # default
    duration_seconds = 15    # default
    fps = 30.0
    reference_video_id = None
    reference_video_path = None

    # YOLO skeleton overlay (YOLO end-to-end)
    from ..models.yolo_pose_detector import YOLOPoseDetector
    from ..utils.yolo_skeleton import draw_yolo_17_skeleton

    try:
        yolo_pose_detector = YOLOPoseDetector(model_name="yolov8n-pose.pt", device=str(config.device))
        yolo_conf_threshold = 0.35
    except Exception as e:
        logger.warning(f"Failed to initialize YOLOPoseDetector for skeleton overlay: {e}")
        yolo_pose_detector = None
        yolo_conf_threshold = 0.35

    def _choose_best_pose(poses):
        if not poses:
            return None
        return max(poses, key=lambda p: float(p.confidence) if p and p.confidence is not None else 0.0)

    # For cancellation / preventing client hangs
    client_stopped = False



    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle configuration message
            if "config" in data:
                if is_recording or frames:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Send config before recording starts"
                    })
                    continue

                config_data = data["config"]
                try:
                    exercise_type, duration_seconds = _validate_recording_config(
                        config_data.get("exercise_type", "squat"),
                        config_data.get("duration_seconds", 15),
                    )
                except HTTPException as exc:
                    await websocket.send_json({
                        "type": "error",
                        "message": exc.detail
                    })
                    continue

                reference_video_id = _parse_reference_video_id(config_data.get("reference_video_id")) if config_data.get("reference_video_id") not in (None, '') else None
                reference_video_path = config_data.get("reference_video_path")

                await websocket.send_json({
                    "type": "config_ack",
                    "message": f"Recording configured for {exercise_type} for {duration_seconds} seconds",
                    "exercise_type": exercise_type,
                    "duration_seconds": duration_seconds,
                    "reference_video_id": reference_video_id,
                    "reference_video_path": reference_video_path
                })
                await websocket.send_json({
                    "type": "recording_started",
                    "message": "Send JPEG frames now",
                    "session_id": session_id
                })
                continue

            # Handle frame message
            if "image" in data:
                image_data = data.get('image')
                if not image_data:
                    continue

                # Decode base64 image
                import base64
                try:
                    # Remove data URL prefix if present
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',')[1]

                    # Decode base64
                    image_bytes = base64.b64decode(image_data)

                    # Convert to numpy array
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if frame is None:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to decode image"
                        })
                        continue

                    # Start recording if not already started
                    if not is_recording:
                        is_recording = True
                        start_time = time.time()
                        last_frame_time = start_time
                        frames = []  # reset frames
                        await websocket.send_json({
                            "type": "recording_started",
                            "message": "Recording started",
                            "timestamp": start_time
                        })

                    # Add frame to recording
                    # Live skeleton overlay: keep YOLO output AND draw it robustly.
                    if yolo_pose_detector is not None:
                        try:
                            poses = yolo_pose_detector.detect(frame)
                            best = _choose_best_pose(poses)
                            if best is not None and best.keypoints:
                                keypoints_xy = [(kp.x, kp.y) for kp in best.keypoints]
                                keypoints_conf = [kp.confidence for kp in best.keypoints]
                                frame = draw_yolo_17_skeleton(
                                    frame,
                                    keypoints_xy,
                                    keypoints_conf,
                                    conf_threshold=yolo_conf_threshold,
                                )
                        except Exception as e:
                            logger.debug(f"YOLO skeleton overlay failed: {e}")
                    frames.append(frame)

                    last_frame_time = time.time()

                    # Check if recording duration has elapsed
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= duration_seconds:
                        # Stop recording and process
                        is_recording = False

                        await websocket.send_json({
                            "type": "recording_stopped",
                            "message": f"Recording stopped after {elapsed_time:.1f} seconds",
                            "frames_captured": len(frames)
                        })

                        # Process the recorded video
                        if len(frames) > 0:
                            try:
                                result = await _process_recorded_video(
                                    frames=frames,
                                    session_id=session_id,
                                    exercise_type=exercise_type,
                                    start_time=start_time,
                                    fps=fps,
                                    duration_seconds=duration_seconds,
                                    reference_video_id=reference_video_id,
                                    reference_video_path=reference_video_path
                                )
                                await websocket.send_json({
                                    "type": "session_complete",
                                    **result
                                })
                            except Exception as e:
                                logger.error(f"Error processing recorded session: {e}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"Error processing session: {str(e)}"
                                })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": "No frames recorded"
                            })

                        # Reset for potential next recording
                        is_recording = False
                        frames = []
                        start_time = None

                except Exception as e:
                    logger.error(f"Error processing frame in recording session: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error processing frame: {str(e)}"
                    })

            # Handle explicit stop message
            elif data.get("command") == "stop":
                if is_recording:
                    is_recording = False
                    elapsed_time = time.time() - start_time if start_time else 0

                    await websocket.send_json({
                        "type": "recording_stopped",
                        "message": f"Recording stopped by client after {elapsed_time:.1f} seconds",
                        "frames_captured": len(frames)
                    })

                    if len(frames) > 0:
                        try:
                            result = await _process_recorded_video(
                                frames=frames,
                                session_id=session_id,
                                exercise_type=exercise_type,
                                start_time=start_time if start_time else time.time(),
                                fps=fps,
                                duration_seconds=duration_seconds,
                                reference_video_id=reference_video_id,
                                reference_video_path=reference_video_path
                            )
                            await websocket.send_json({
                                "type": "session_complete",
                                **result
                            })
                        except Exception as e:
                            logger.error(f"Error processing recorded session: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Error processing session: {str(e)}"
                            })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No frames recorded"
                        })

                    # Reset state
                    is_recording = False
                    frames = []
                    start_time = None
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Not currently recording"
                    })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Error in recording session WebSocket: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Server error: {str(e)}"
            })
        except:
            pass  # Ignore if we can't send error message


# If youtube_routes module is present, wire its routes too
try:
    from .youtube_routes import setup_youtube_routes
    setup_youtube_routes(app)
except Exception as e:
    logger.info(f"YouTube route registration skipped: {e}")