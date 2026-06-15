import torch
import numpy as np
from typing import List, Tuple, Any
from transformers import AutoModelForObjectDetection, AutoImageProcessor
from PIL import Image
import cv2

try:
    from .base_detector import BaseDetector, Detection
except ImportError:
    from base_detector import BaseDetector, Detection

class HuggingFaceDetector(BaseDetector):
    def __init__(self, model_id: str, **kwargs):
        super().__init__(model_name=model_id, **kwargs)
        self.model_id = model_id
        self.image_processor = None
        self.load_model()
    
    def load_model(self):
        """Load HuggingFace model"""
        print(f"Loading HuggingFace model: {self.model_id}")
        
        # Available HuggingFace models for object detection
        # "facebook/detr-resnet-50"
        # "hustvl/yolos-small"
        # "microsoft/table-transformer-detection"
        # "google/owlvit-base-patch32"
        
        self.image_processor = AutoImageProcessor.from_pretrained(
            self.model_id,
            cache_dir=self.kwargs.get('cache_dir', './models')
        )
        
        self._model = AutoModelForObjectDetection.from_pretrained(
            self.model_id,
            cache_dir=self.kwargs.get('cache_dir', './models')
        ).to(self.device)
        
        self._model.eval()
        
        # Get class names
        if hasattr(self._model.config, 'id2label'):
            self.class_names = list(self._model.config.id2label.values())
        else:
            self.class_names = ['person']  # Default
    
    def preprocess(self, frame: np.ndarray) -> torch.Tensor:
        """Convert frame to model input format"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        # Process image
        inputs = self.image_processor(images=pil_image, return_tensors="pt")
        return inputs.to(self.device)
    
    def predict(self, processed_input: Any) -> dict:
        """Run inference"""
        with torch.no_grad():
            if self.kwargs.get('enable_fp16', False):
                with torch.autocast(device_type=self.device):
                    outputs = self._model(**processed_input)
            else:
                outputs = self._model(**processed_input)
        return outputs
    
    def postprocess(self, predictions: dict, frame_shape: Tuple[int, int]) -> List[Detection]:
        """Convert model outputs to detections"""
        height, width = frame_shape
        
        # Process outputs (different models have different output formats)
        if hasattr(self._model.config, 'model_type'):
            if self._model.config.model_type == 'detr':
                return self._process_detr(predictions, width, height)
            elif self._model.config.model_type == 'yolos':
                return self._process_yolos(predictions, width, height)
        
        # Default processing
        return self._process_generic(predictions, width, height)
    
    def _process_detr(self, predictions: dict, width: int, height: int) -> List[Detection]:
        """Process DETR model outputs"""
        detections = []
        
        # DETR returns logits and bounding boxes
        logits = predictions.logits[0]
        boxes = predictions.pred_boxes[0]
        
        # Get predictions with sufficient confidence
        prob = logits.softmax(-1)
        scores, labels = prob[..., :-1].max(-1)
        
        # Convert boxes from [center_x, center_y, width, height] to [x1, y1, x2, y2]
        for score, label, box in zip(scores, labels, boxes):
            if score >= self.confidence_threshold:
                cx, cy, w, h = box.tolist()
                
                x1 = (cx - w / 2) * width
                y1 = (cy - h / 2) * height
                x2 = (cx + w / 2) * width
                y2 = (cy + h / 2) * height
                
                class_name = self.class_names[label] if label < len(self.class_names) else f"class_{label}"
                
                detections.append(Detection(
                    bbox=[x1, y1, x2, y2],
                    confidence=float(score),
                    class_id=int(label),
                    class_name=class_name
                ))
        
        return detections
    
    def _process_yolos(self, predictions: dict, width: int, height: int) -> List[Detection]:
        """Process YOLOS model outputs"""
        detections = []
        
        # Similar to DETR but with different output format
        results = self.image_processor.post_process_object_detection(
            predictions,
            threshold=self.confidence_threshold,
            target_sizes=[(height, width)]
        )[0]
        
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            x1, y1, x2, y2 = box.tolist()
            
            class_name = self.class_names[label] if label < len(self.class_names) else f"class_{label}"
            
            detections.append(Detection(
                bbox=[x1, y1, x2, y2],
                confidence=float(score),
                class_id=int(label),
                class_name=class_name
            ))
        
        return detections
    
    def _process_generic(self, predictions: dict, width: int, height: int) -> List[Detection]:
        """Generic processing for other models"""
        detections = []
        
        # Try to extract common patterns
        if hasattr(predictions, 'boxes'):
            boxes = predictions.boxes
            for box in boxes:
                # Extract bbox, confidence, class
                if len(box) >= 6:  # x1, y1, x2, y2, conf, class
                    x1, y1, x2, y2, conf, cls = box[:6]
                    
                    detections.append(Detection(
                        bbox=[float(x1) * width, float(y1) * height, 
                              float(x2) * width, float(y2) * height],
                        confidence=float(conf),
                        class_id=int(cls),
                        class_name=self.class_names[int(cls)] if int(cls) < len(self.class_names) else f"class_{cls}"
                    ))
        
        return detections