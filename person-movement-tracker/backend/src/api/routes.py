from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from typing import List, Optional, Dict
import asyncio
import json
import logging
import os
import tempfile
import time
import numpy as np
import cv2

logger = logging.getLogger(__name__)

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

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await tracking_service.initialize()
    global exercise_tracking_service, video_analysis_service, background_form_detector
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
        classifier_model = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "form_classifier_model.pkl")
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
        guidance_service = GuidanceService()

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

        ai_summary = guidance_service.generate_guidance(
            exercise_type=exercise_type,
            user_summary={
                'overall_form_score': user_result.overall_form_score,
                'summary': user_result.summary
            },
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
        'classifier': 'xgboost' if background_form_detector.classifier and background_form_detector.classifier.is_trained else 'heuristic'
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


# If youtube_routes module is present, wire its routes too
try:
    from .youtube_routes import setup_youtube_routes
    setup_youtube_routes(app)
except Exception as e:
    logger.info(f"YouTube route registration skipped: {e}")