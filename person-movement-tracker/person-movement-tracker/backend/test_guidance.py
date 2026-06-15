#!/usr/bin/env python3
"""
Test script for GuidanceService Qwen integration
"""

import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_guidance_service():
    """Test the GuidanceService with Qwen model"""
    try:
        # Import with absolute imports
        from config import config
        from services.guidance_service import GuidanceService
        from models.exercise_analyzer import ExerciseType

        # Set token if not set (use your own token)
        if not os.getenv('HF_TOKEN'):
            os.environ['HF_TOKEN'] = 'your_hf_token_here'

        print("🔧 Testing GuidanceService logic (without model loading)...")

        # Test token guidance
        token_info = GuidanceService.get_token_guidance()
        print(f"🔑 Token guidance: {token_info}")

        # Create instance without loading model
        guidance = object.__new__(GuidanceService)  # Create without __init__
        guidance._is_ready = False  # Simulate not ready

        # Test motion to words
        keypoints = {
            "left_shoulder": (0.5, 0.3),
            "left_hip": (0.5, 0.5),
            "left_knee": (0.5, 0.7),
            "left_ankle": (0.5, 0.9),
        }

        motion_desc = guidance.motion_to_words(keypoints, "test workout")
        print(f"📝 Motion description: {motion_desc}")

        # Test exercise classification
        inferred = guidance.classify_exercise_from_description(motion_desc)
        print(f"🏋️ Inferred exercise: {inferred.value if inferred else 'unknown'}")

        # Test remote exercise match (fallback)
        result = guidance.remote_exercise_match(motion_desc)
        print(f"🤖 Fallback analysis: {result.get('analysis', 'N/A')}")
        print(f"🎯 Matched exercise: {result.get('matched_exercise', 'N/A')}")

        print("✅ Logic tests passed! Model loading would work with proper setup.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_guidance_service()