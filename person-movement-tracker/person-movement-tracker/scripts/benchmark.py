#!/usr/bin/env python3
"""
Performance benchmark for Person Movement Tracker
"""
import time
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.src.models.detector_factory import DetectorFactory, ModelType
from backend.src.models.tracker import MultiObjectTracker
from backend.src.utils.image_processor import ImageProcessor
from backend.src.utils.device_optimizer import DeviceOptimizer

def benchmark_detector(model_type, iterations=100):
    """Benchmark a detector model"""
    print(f"\nBenchmarking {model_type.value}...")
    print("-" * 60)
    
    try:
        # Create detector
        detector = DetectorFactory.create_detector(
            model_type,
            device="cpu",
            confidence_threshold=0.5
        )
        
        # Warmup
        print("Warming up...")
        dummy_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        for _ in range(10):
            detector.detect(dummy_frame)
        
        # Benchmark
        print(f"Running {iterations} iterations...")
        times = []
        
        for i in range(iterations):
            frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
            
            start = time.time()
            result = detector.detect(frame)
            end = time.time()
            
            times.append(end - start)
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{iterations}")
        
        # Statistics
        times = np.array(times)
        avg_time = np.mean(times)
        std_time = np.std(times)
        min_time = np.min(times)
        max_time = np.max(times)
        fps = 1.0 / avg_time
        
        print(f"\nResults for {model_type.value}:")
        print(f"  Average inference time: {avg_time * 1000:.2f}ms")
        print(f"  Std deviation: {std_time * 1000:.2f}ms")
        print(f"  Min time: {min_time * 1000:.2f}ms")
        print(f"  Max time: {max_time * 1000:.2f}ms")
        print(f"  FPS: {fps:.2f}")
        
        return {
            'model': model_type.value,
            'avg_time': avg_time,
            'std_time': std_time,
            'min_time': min_time,
            'max_time': max_time,
            'fps': fps
        }
        
    except Exception as e:
        print(f"Error benchmarking {model_type.value}: {e}")
        return None

def benchmark_tracker(iterations=100):
    """Benchmark the tracker"""
    print("\nBenchmarking Tracker...")
    print("-" * 60)
    
    try:
        tracker = MultiObjectTracker(tracker_type="deepsort")
        
        # Create mock detections
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        times = []
        
        for i in range(iterations):
            # Create random detections
            num_detections = np.random.randint(1, 5)
            detections = []
            
            for _ in range(num_detections):
                x1 = np.random.randint(0, 400)
                y1 = np.random.randint(0, 300)
                x2 = x1 + np.random.randint(50, 150)
                y2 = y1 + np.random.randint(50, 150)
                
                from backend.src.models.base_detector import Detection
                detections.append(Detection(
                    bbox=[x1, y1, x2, y2],
                    confidence=np.random.uniform(0.5, 0.95),
                    class_id=0,
                    class_name='person'
                ))
            
            start = time.time()
            tracker.update(detections, frame)
            end = time.time()
            
            times.append(end - start)
        
        times = np.array(times)
        avg_time = np.mean(times)
        
        print(f"  Average tracking time: {avg_time * 1000:.2f}ms")
        print(f"  FPS: {1.0 / avg_time:.2f}")
        
        return {
            'avg_time': avg_time,
            'fps': 1.0 / avg_time
        }
        
    except Exception as e:
        print(f"Error benchmarking tracker: {e}")
        return None

def main():
    print("=" * 60)
    print("Person Movement Tracker - Performance Benchmark")
    print("=" * 60)
    
    # Device info
    optimizer = DeviceOptimizer()
    device_info = optimizer.get_performance_metrics()
    
    print("\nDevice Information:")
    print(f"  Device: {device_info['recommended_device']}")
    print(f"  CPU Count: {device_info['system_info']['cpu_count']}")
    print(f"  Memory: {device_info['system_info']['memory_gb']:.2f} GB")
    
    # Benchmark models
    results = []
    
    for model_type in [ModelType.YOLOv8, ModelType.DETR]:
        result = benchmark_detector(model_type, iterations=50)
        if result:
            results.append(result)
    
    # Benchmark tracker
    tracker_result = benchmark_tracker(iterations=50)
    
    # Summary
    print("\n" + "=" * 60)
    print("Benchmark Summary")
    print("=" * 60)
    
    for result in results:
        print(f"\n{result['model'].upper()}:")
        print(f"  Inference: {result['avg_time'] * 1000:.2f}ms ({result['fps']:.2f} FPS)")
    
    if tracker_result:
        print(f"\nTracker:")
        print(f"  Update: {tracker_result['avg_time'] * 1000:.2f}ms ({tracker_result['fps']:.2f} FPS)")

if __name__ == "__main__":
    main()