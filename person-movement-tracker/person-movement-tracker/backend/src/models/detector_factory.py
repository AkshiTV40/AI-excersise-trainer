from typing import Dict, Any

try:
    from ..config import ModelType, DeviceType
    from .yolo_detector import YOLODetector
    from .huggingface_detector import HuggingFaceDetector
except ImportError:
    from config import ModelType, DeviceType
    from models.yolo_detector import YOLODetector
    from models.huggingface_detector import HuggingFaceDetector

class DetectorFactory:
    """Factory for creating detector instances"""
    
    _model_registry = {
        ModelType.YOLOv8: {
            'class': YOLODetector,
            'default_args': {
                'model_path': 'yolov8n.pt',
                'confidence_threshold': 0.5,
                'iou_threshold': 0.45
            }
        },
        ModelType.DETR: {
            'class': HuggingFaceDetector,
            'default_args': {
                'model_id': 'facebook/detr-resnet-50',
                'confidence_threshold': 0.5
            }
        },
        ModelType.YOLOS: {
            'class': HuggingFaceDetector,
            'default_args': {
                'model_id': 'hustvl/yolos-small',
                'confidence_threshold': 0.5
            }
        }
    }
    
    @classmethod
    def create_detector(cls, 
                       model_type: ModelType,
                       device: str = "cpu",
                       **kwargs) -> Any:
        """Create a detector instance"""
        
        if model_type not in cls._model_registry:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model_info = cls._model_registry[model_type]
        model_class = model_info['class']
        default_args = model_info['default_args'].copy()
        
        # Update with provided kwargs
        default_args.update(kwargs)
        
        # Create instance
        detector = model_class(**default_args)
        
        return detector
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Dict]:
        """Get list of available models"""
        return {
            name: {
                'description': cls._get_model_description(name),
                'supports_tracking': cls._supports_tracking(name)
            }
            for name in cls._model_registry.keys()
        }
    
    @classmethod
    def _get_model_description(cls, model_type: ModelType) -> str:
        """Get description for each model"""
        descriptions = {
            ModelType.YOLOv8: "YOLOv8 - Fast, accurate object detection with tracking support",
            ModelType.DETR: "DETR (DEtection TRansformer) - Transformer-based detection",
            ModelType.YOLOS: "YOLOS - Vision Transformer for object detection"
        }
        return descriptions.get(model_type, "Unknown model")
    
    @classmethod
    def _supports_tracking(cls, model_type: ModelType) -> bool:
        """Check if model supports tracking"""
        return model_type == ModelType.YOLOv8