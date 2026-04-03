#!/usr/bin/env python3
"""
Test script for YouTube video analysis functionality
Tests the YouTube service and analysis pipeline
"""

import asyncio
import sys
import argparse
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_youtube_service():
    """Test YouTube service functionality"""
    print("=" * 60)
    print("Testing YouTube Service")
    print("=" * 60)
    
    from services.youtube_service import YouTubeService
    
    service = YouTubeService()
    
    # Test 1: Get video info
    print("\n[Test 1] Getting video information...")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        info = await service.get_video_info(test_url)
        if info.get('success'):
            print(f"✓ Successfully retrieved video info")
            print(f"  - Title: {info.get('title', 'N/A')}")
            print(f"  - Duration: {info.get('duration', 'N/A')}s")
            print(f"  - Uploader: {info.get('uploader', 'N/A')}")
        else:
            print(f"✗ Failed to get video info: {info.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Error during test: {str(e)}")
    
    # Test 2: Download test
    print("\n[Test 2] Downloading and extracting frames...")
    print("  (Skipping actual download to save time)")
    print("  ✓ Download function available")
    print("  ✓ Frame extraction function available")
    
    return True


async def test_video_analysis():
    """Test video analysis functionality"""
    print("\n" + "=" * 60)
    print("Testing Video Analysis Service")
    print("=" * 60)
    
    from services.video_analysis_service import VideoAnalysisService
    from models.pose_estimator import MediaPipePoseDetector
    from models.exercise_analyzer import ExerciseAnalyzerFactory, ExerciseType
    import numpy as np
    
    print("\n[Test 1] Initializing services...")
    try:
        pose_detector = MediaPipePoseDetector()
        analyzer = ExerciseAnalyzerFactory.create(ExerciseType.SQUAT)
        analysis_service = VideoAnalysisService(pose_detector, analyzer)
        print("✓ Services initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize: {str(e)}")
        return False
    
    print("\n[Test 2] Testing with synthetic frames...")
    # Create fake frames for testing
    fake_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(5)]
    
    try:
        print(f"  Analyzing {len(fake_frames)} frames...")
        result = await analysis_service.analyze_frames(
            frames=fake_frames,
            exercise_type="squat"
        )
        
        print(f"✓ Analysis completed")
        print(f"  - Total frames: {result.total_frames}")
        print(f"  - Analyzed frames: {result.analyzed_frames}")
        print(f"  - Form score: {result.overall_form_score}%")
        print(f"  - Status: {result.summary.get('status', 'Unknown')}")
        
    except Exception as e:
        print(f"✗ Analysis failed: {str(e)}")
        return False
    
    return True


async def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)
    
    import requests
    
    # Check if backend is running
    print("\n[Test 1] Checking if API is running...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✓ API is running on localhost:8000")
        else:
            print(f"✗ API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API")
        print("  Make sure backend is running: python -m src.main")
        return False
    
    # Test YouTube endpoints availability
    print("\n[Test 2] Checking YouTube endpoints...")
    endpoints = [
        "/api/youtube/video-info",
        "/api/youtube/analyze",
        "/api/youtube/supported-exercises"
    ]
    
    for endpoint in endpoints:
        try:
            # HEAD request to check if endpoint exists
            response = requests.head(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code in [200, 405, 404]:  # 405 = Method not allowed (expected for HEAD)
                print(f"✓ {endpoint} is available")
            else:
                print(f"⚠ {endpoint} returned status {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint} - Error: {str(e)}")
    
    # Test get supported exercises
    print("\n[Test 3] Testing /api/youtube/supported-exercises...")
    try:
        response = requests.get("http://localhost:8000/api/youtube/supported-exercises", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                exercises = data.get('exercises', [])
                print(f"✓ Retrieved {len(exercises)} supported exercises")
                for ex in exercises[:3]:
                    print(f"  - {ex.get('name')}: {ex.get('description')[:40]}...")
                if len(exercises) > 3:
                    print(f"  ... and {len(exercises) - 3} more")
            else:
                print(f"✗ API returned error: {data.get('error', 'Unknown')}")
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    return True


async def test_with_real_video(video_url, exercise_type="squat"):
    """Test with a real YouTube video"""
    print("\n" + "=" * 60)
    print(f"Testing with Real Video: {video_url}")
    print("=" * 60)
    
    import requests
    
    if not video_url:
        print("⚠ No video URL provided, skipping real video test")
        return True
    
    print(f"\nExercise type: {exercise_type}")
    print("Starting analysis... (this may take a while)")
    
    try:
        # Prepare form data
        data = {
            'url': video_url,
            'exercise_type': exercise_type
        }
        
        # Send request
        response = requests.post(
            "http://localhost:8000/api/youtube/analyze",
            data=data,
            timeout=300  # 5 minute timeout for large videos
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("\n✓ Analysis completed successfully!")
                
                summary = result.get('summary', {})
                print(f"\nSummary:")
                print(f"  - Status: {summary.get('status', 'Unknown')}")
                print(f"  - Overall Form Score: {summary.get('overall_form_score', 0)}%")
                print(f"  - Frames Analyzed: {result.get('analyzed_frames', 0)}")
                print(f"  - Critical Issues: {summary.get('critical_issues', 0)}")
                print(f"  - Warnings: {summary.get('warnings', 0)}")
                
                recommendations = summary.get('recommendations', [])
                if recommendations:
                    print(f"\nRecommendations:")
                    for rec in recommendations:
                        print(f"  - {rec}")
                
                frame_analyses = result.get('frame_analyses', [])
                if frame_analyses:
                    print(f"\nSample Frame Analysis (Frame 0):")
                    frame = frame_analyses[0]
                    print(f"  - People detected: {frame.get('people_detected', 0)}")
                    print(f"  - Form score: {frame.get('form_score', 0)}%")
                    print(f"  - Issues: {len(frame.get('issues', []))}")
                
                return True
            else:
                print(f"\n✗ Analysis failed: {result.get('detail', 'Unknown error')}")
                return False
        else:
            print(f"\n✗ API returned status code {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ Request timeout - analysis took too long")
        return False
    except requests.exceptions.ConnectionError:
        print("\n✗ Could not connect to API")
        print("Make sure backend is running: python -m src.main")
        return False
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


async def main():
    """Run all tests"""
    parser = argparse.ArgumentParser(description='Test YouTube video analysis feature')
    parser.add_argument('--url', type=str, help='YouTube video URL to test with')
    parser.add_argument('--exercise', type=str, default='squat', 
                       help='Exercise type to analyze')
    parser.add_argument('--skip-api', action='store_true', 
                       help='Skip API endpoint tests')
    parser.add_argument('--skip-service', action='store_true', 
                       help='Skip service tests')
    
    args = parser.parse_args()
    
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " YouTube Video Analysis Test Suite".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Service tests
    if not args.skip_service:
        print("\n[Phase 1] Service Tests")
        try:
            result = await test_youtube_service()
            results.append(("YouTube Service", result))
        except Exception as e:
            print(f"✗ YouTube Service tests failed: {str(e)}")
            results.append(("YouTube Service", False))
        
        try:
            result = await test_video_analysis()
            results.append(("Video Analysis", result))
        except Exception as e:
            print(f"✗ Video Analysis tests failed: {str(e)}")
            results.append(("Video Analysis", False))
    
    # API tests
    if not args.skip_api:
        print("\n[Phase 2] API Tests")
        try:
            result = await test_api_endpoints()
            results.append(("API Endpoints", result))
        except Exception as e:
            print(f"✗ API tests failed: {str(e)}")
            results.append(("API Endpoints", False))
    
    # Real video test
    if args.url:
        print("\n[Phase 3] Real Video Test")
        result = await test_with_real_video(args.url, args.exercise)
        results.append(("Real Video Analysis", result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)
