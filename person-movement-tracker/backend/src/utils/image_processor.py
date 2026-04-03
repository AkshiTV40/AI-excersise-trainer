import cv2
import numpy as np
import base64
from typing import Tuple, Optional

try:
    from ..config import config
except ImportError:
    from config import config

class ImageProcessor:
    def __init__(self):
        self.max_frame_size = config.max_frame_size
        self.mobile_frame_size = config.mobile_frame_size
    
    def decode_base64(self, image_data: str) -> np.ndarray:
        """Decode base64 image data to numpy array"""
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            # Convert to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            # Decode image
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                raise ValueError("Failed to decode image")
            
            return frame
            
        except Exception as e:
            raise ValueError(f"Error decoding image: {str(e)}")
    
    def encode_base64(self, frame: np.ndarray) -> str:
        """Encode numpy array to base64 string"""
        try:
            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # Convert to base64
            image_data = base64.b64encode(buffer).decode('utf-8')
            
            return image_data
            
        except Exception as e:
            raise ValueError(f"Error encoding image: {str(e)}")
    
    def optimize_for_device(self, frame: np.ndarray) -> np.ndarray:
        """Optimize frame size based on device capabilities"""
        height, width = frame.shape[:2]
        
        # Determine target size based on device
        if config.device == "cpu":
            # Reduce size for CPU processing
            target_width, target_height = self.mobile_frame_size
        else:
            # Use max size for GPU
            target_width, target_height = self.max_frame_size
        
        # Calculate scaling factor
        scale_x = target_width / width
        scale_y = target_height / height
        scale = min(scale_x, scale_y)
        
        if scale < 1.0:
            # Only downscale, never upscale
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        return frame
    
    def detect_device_type(self) -> str:
        """Detect device type for optimization"""
        import torch
        
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def get_frame_info(self, frame: np.ndarray) -> dict:
        """Get frame information"""
        height, width = frame.shape[:2]
        
        return {
            'width': width,
            'height': height,
            'channels': frame.shape[2] if len(frame.shape) > 2 else 1,
            'size_mb': frame.nbytes / (1024 * 1024)
        }
    
    def draw_bounding_boxes(self, 
                          frame: np.ndarray, 
                          detections: list,
                          colors: Optional[dict] = None) -> np.ndarray:
        """Draw bounding boxes on frame"""
        frame_copy = frame.copy()
        
        if colors is None:
            colors = {}
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            confidence = det.get('confidence', 0.0)
            class_name = det.get('class_name', 'unknown')
            track_id = det.get('track_id')
            
            # Choose color
            if track_id is not None:
                color = colors.get(track_id, (255, 0, 0))
            else:
                color = (0, 255, 0)
            
            # Draw bounding box
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name} {confidence:.2f}"
            if track_id is not None:
                label = f"ID:{track_id} {label}"
            
            # Draw label background
            (label_width, label_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            
            cv2.rectangle(frame_copy, (x1, y1 - label_height - 10), 
                         (x1 + label_width, y1), color, -1)
            
            # Draw label text
            cv2.putText(frame_copy, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame_copy