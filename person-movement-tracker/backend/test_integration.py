"""
Integration test for YouTube analysis feature
Verifies all components work together
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


async def test_imports():
    """Test that all required modules import correctly"""
    print("Testing imports...")
    try:
        from services.youtube_service import YouTubeService
        print("✓ YouTubeService imported")
        
        from services.video_analysis_service import VideoAnalysisService
        print("✓ VideoAnalysisService imported")
        
        from models.pose_estimator import MediaPipePoseDetector
        print("✓ MediaPipePoseDetector imported")
        
        from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
        print("✓ ExerciseAnalyzerFactory imported")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {str(e)}")
        return False


async def test_service_initialization():
    """Test that services can be initialized"""
    print("\nTesting service initialization...")
    try:
        from services.youtube_service import YouTubeService
        from services.video_analysis_service import VideoAnalysisService
        from models.pose_estimator import MediaPipePoseDetector
        from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
        
        # Initialize YouTube service
        youtube_service = YouTubeService()
        print("✓ YouTubeService initialized")
        
        # Initialize pose detector
        pose_detector = MediaPipePoseDetector()
        print("✓ MediaPipePoseDetector initialized")
        
        # Initialize exercise analyzer
        analyzer = ExerciseAnalyzerFactory.create(ExerciseType.SQUAT)
        print("✓ ExerciseAnalyzerFactory initialized")
        
        # Initialize video analysis service
        analysis_service = VideoAnalysisService(pose_detector, analyzer)
        print("✓ VideoAnalysisService initialized")
        
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_exercise_types():
    """Test that all exercise types are supported"""
    print("\nTesting exercise types...")
    try:
        from models.exercise_analyzer import ExerciseType
        
        exercises = [e.value for e in ExerciseType]
        print(f"✓ Found {len(exercises)} supported exercise types:")
        for ex in exercises:
            print(f"  - {ex}")
        
        return len(exercises) > 0
    except Exception as e:
        print(f"✗ Exercise type test failed: {str(e)}")
        return False


async def test_analysis_pipeline():
    """Test the complete analysis pipeline with dummy data"""
    print("\nTesting analysis pipeline...")
    try:
        import numpy as np
        from services.video_analysis_service import VideoAnalysisService
        from models.pose_estimator import MediaPipePoseDetector
        from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
        
        # Create fake frame
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Initialize services
        pose_detector = MediaPipePoseDetector()
        analyzer = ExerciseAnalyzerFactory.create(ExerciseType.SQUAT)
        analysis_service = VideoAnalysisService(pose_detector, analyzer)
        
        # Run analysis
        result = await analysis_service.analyze_frames(
            frames=[fake_frame],
            exercise_type="squat"
        )
        
        print(f"✓ Analysis pipeline completed")
        print(f"  - Total frames: {result.total_frames}")
        print(f"  - Analyzed frames: {result.analyzed_frames}")
        print(f"  - Form score: {result.overall_form_score}%")
        print(f"  - Summary available: {bool(result.summary)}")
        
        return True
    except Exception as e:
        print(f"✗ Analysis pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_youtube_service_methods():
    """Test YouTube service methods"""
    print("\nTesting YouTube service methods...")
    try:
        from services.youtube_service import YouTubeService
        
        service = YouTubeService()
        
        # Check methods exist
        methods = [
            'fetch_video',
            'get_video_info',
            'extract_frames',
            'cleanup_video',
            'cleanup_all'
        ]
        
        for method in methods:
            if hasattr(service, method) and callable(getattr(service, method)):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"✗ YouTube service method test failed: {str(e)}")
        return False


async def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from config import config
        
        print(f"✓ Config loaded")
        print(f"  - API host: {config.api_host}")
        print(f"  - API port: {config.api_port}")
        print(f"  - Debug mode: {config.debug}")
        print(f"  - CORS origins: {config.cors_origins[:2]}...")
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {str(e)}")
        return False


async def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("YouTube Analysis Feature - Integration Tests")
    print("="*60 + "\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("Service Initialization", test_service_initialization),
        ("Exercise Types", test_exercise_types),
        ("Analysis Pipeline", test_analysis_pipeline),
        ("YouTube Service Methods", test_youtube_service_methods),
        ("Configuration", test_config),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
            import traceback
            traceback.print_exc()
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ All integration tests passed!")
        print("\nYou can now:")
        print("1. Run the backend: python -m src.main")
        print("2. Run the frontend: npm run dev")
        print("3. Test YouTube analysis: test_youtube_analysis.py --url <youtube_url>")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
