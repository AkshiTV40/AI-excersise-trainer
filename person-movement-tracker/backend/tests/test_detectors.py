import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pytest
from models.base_detector import BaseDetector, Detection
from models.detector_factory import DetectorFactory, ModelType

class MockDetector(BaseDetector):
    def load_model(self):
        pass
    
    def preprocess(self, frame):
        return frame
    
    def predict(self, processed_input):
        return processed_input
    
    def postprocess(self, predictions, frame_shape):
        return [
            Detection(
                bbox=[100, 100, 200, 200],
                confidence=0.9,
                class_id=0,
                class_name='person'
            )
        ]

def test_detection_dataclass():
    det = Detection(
        bbox=[100, 100, 200, 200],
        confidence=0.9,
        class_id=0,
        class_name='person',
        track_id=1
    )
    
    assert det.bbox == [100, 100, 200, 200]
    assert det.confidence == 0.9
    assert det.class_id == 0
    assert det.class_name == 'person'
    assert det.track_id == 1

def test_mock_detector():
    detector = MockDetector('test_model', device='cpu')
    
    # Create dummy frame
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Run detection
    result = detector.detect(frame)
    
    assert result.model_name == 'test_model'
    assert len(result.detections) == 1
    assert result.frame_shape == (480, 640)
    assert result.inference_time >= 0

def test_filter_detections():
    detector = MockDetector('test_model', device='cpu', confidence_threshold=0.5)
    
    detections = [
        Detection([100, 100, 200, 200], 0.9, 0, 'person'),
        Detection([300, 300, 400, 400], 0.3, 0, 'person'),
        Detection([500, 500, 600, 600], 0.7, 1, 'car')
    ]
    
    # Filter by confidence
    filtered = detector.filter_detections(detections)
    assert len(filtered) == 2
    
    # Filter by class
    filtered = detector.filter_detections(detections, class_filter=[0])
    assert len(filtered) == 1
    assert filtered[0].class_id == 0

def test_detector_factory_get_available_models():
    models = DetectorFactory.get_available_models()
    
    assert ModelType.YOLOv8 in models
    assert ModelType.DETR in models
    assert ModelType.YOLOS in models
    
    for model_type, info in models.items():
        assert 'description' in info
        assert 'supports_tracking' in info

def test_detector_factory_create_detector():
    # This test requires actual models to be downloaded
    # Skipping for unit tests
    pytest.skip("Requires model download")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])