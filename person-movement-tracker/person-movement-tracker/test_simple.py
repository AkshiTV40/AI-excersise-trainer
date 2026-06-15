#!/usr/bin/env python3
"""
Simple test script to verify the project structure and basic functionality
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config import config
        print("  Config: OK")
    except Exception as e:
        print(f"  Config: FAILED - {e}")
        return False
    
    try:
        from models.base_detector import BaseDetector, Detection, ModelResult
        print("  Base Detector: OK")
    except Exception as e:
        print(f"  Base Detector: FAILED - {e}")
        return False
    
    try:
        from models.detector_factory import DetectorFactory, ModelType
        print("  Detector Factory: OK")
    except Exception as e:
        print(f"  Detector Factory: FAILED - {e}")
        return False
    
    try:
        from api.schemas import TrackingRequest, TrackingResponse, ModelInfo
        print("  API Schemas: OK")
    except Exception as e:
        print(f"  API Schemas: FAILED - {e}")
        return False
    
    return True

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    
    from config import config
    
    print(f"  API Host: {config.api_host}")
    print(f"  API Port: {config.api_port}")
    print(f"  Default Model: {config.default_model}")
    print(f"  Device: {config.device}")
    
    return True

def test_detector_factory():
    """Test detector factory"""
    print("\nTesting detector factory...")
    
    from models.detector_factory import DetectorFactory, ModelType
    
    models = DetectorFactory.get_available_models()
    print(f"  Available models: {len(models)}")
    
    for model_type, info in models.items():
        print(f"    - {model_type.value}: {info['description']}")
    
    return True

def test_schemas():
    """Test Pydantic schemas"""
    print("\nTesting schemas...")
    
    from api.schemas import TrackingRequest, ModelInfo
    
    # Test ModelInfo
    model_info = ModelInfo(
        name="yolov8",
        description="Test model",
        supports_tracking=True
    )
    print(f"  ModelInfo created: {model_info.name}")
    
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting file structure...")
    
    base_path = Path(__file__).parent
    
    required_files = [
        "backend/src/main.py",
        "backend/src/config.py",
        "backend/requirements.txt",
        "backend/Dockerfile",
        "frontend/package.json",
        "frontend/vite.config.js",
        "frontend/src/App.jsx",
        "docker-compose.yml",
        "README.md",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  {file_path}: EXISTS")
        else:
            print(f"  {file_path}: MISSING")
            all_exist = False
    
    return all_exist

def main():
    print("=" * 60)
    print("Person Movement Tracker - Simple Test Suite")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Detector Factory", test_detector_factory),
        ("Schemas", test_schemas),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! The project is ready to use.")
        return 0
    else:
        print("\nSome tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())