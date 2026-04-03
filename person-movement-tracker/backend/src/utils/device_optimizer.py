import torch
import psutil
import platform
from typing import Dict, Any

try:
    from ..config import config
except ImportError:
    from config import config

class DeviceOptimizer:
    def __init__(self):
        self.system_info = self._get_system_info()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        info = {
            'platform': platform.system(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'available_memory_gb': psutil.virtual_memory().available / (1024**3)
        }
        
        # GPU information
        if torch.cuda.is_available():
            info['cuda_version'] = torch.version.cuda
            info['gpu_count'] = torch.cuda.device_count()
            info['gpu_name'] = torch.cuda.get_device_name(0)
            info['gpu_memory_gb'] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        else:
            info['cuda_available'] = False
        
        # Apple Silicon
        if hasattr(torch.backends, 'mps'):
            info['mps_available'] = torch.backends.mps.is_available()
        else:
            info['mps_available'] = False
        
        return info
    
    def recommend_device(self) -> str:
        """Recommend the best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def get_optimal_batch_size(self, device: str) -> int:
        """Get optimal batch size for device"""
        if device == "cuda":
            gpu_memory = self.system_info.get('gpu_memory_gb', 0)
            if gpu_memory > 8:
                return 8
            elif gpu_memory > 4:
                return 4
            else:
                return 2
        elif device == "mps":
            return 4  # Apple Silicon optimization
        else:
            # CPU - smaller batches
            cpu_count = self.system_info.get('cpu_count', 4)
            return min(2, cpu_count // 2)
    
    def get_optimal_model_size(self, device: str) -> str:
        """Recommend model size based on device"""
        if device == "cuda":
            gpu_memory = self.system_info.get('gpu_memory_gb', 0)
            if gpu_memory > 8:
                return "large"  # yolov8l, detr-resnet-101
            elif gpu_memory > 4:
                return "medium"  # yolov8m, detr-resnet-50
            else:
                return "small"  # yolov8n, yolos-small
        elif device == "mps":
            return "medium"  # Apple Silicon can handle medium models
        else:
            return "small"  # CPU optimized
    
    def should_use_fp16(self, device: str) -> bool:
        """Check if FP16 should be used"""
        if device == "cuda":
            # Check if GPU supports FP16
            gpu_name = self.system_info.get('gpu_name', '').lower()
            # Modern GPUs support FP16
            return 'rtx' in gpu_name or 'gtx' in gpu_name or 'titan' in gpu_name
        return False
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        memory = psutil.virtual_memory()
        
        usage = {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'percentage': memory.percent
        }
        
        if torch.cuda.is_available():
            usage['gpu_memory_allocated_gb'] = torch.cuda.memory_allocated() / (1024**3)
            usage['gpu_memory_reserved_gb'] = torch.cuda.memory_reserved() / (1024**3)
        
        return usage
    
    def optimize_frame_size(self, device: str, original_size: tuple) -> tuple:
        """Optimize frame size for device"""
        width, height = original_size
        
        if device == "cpu":
            # Reduce size for CPU
            max_size = 640
        elif device == "cuda":
            gpu_memory = self.system_info.get('gpu_memory_gb', 0)
            if gpu_memory > 8:
                max_size = 1280
            elif gpu_memory > 4:
                max_size = 960
            else:
                max_size = 640
        else:
            max_size = 960  # MPS or unknown
        
        # Calculate scaling
        scale = min(max_size / width, max_size / height)
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            return (new_width, new_height)
        
        return original_size
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'system_info': self.system_info,
            'recommended_device': self.recommend_device(),
            'memory_usage': self.get_memory_usage(),
            'optimal_batch_size': self.get_optimal_batch_size(self.recommend_device()),
            'optimal_model_size': self.get_optimal_model_size(self.recommend_device()),
            'use_fp16': self.should_use_fp16(self.recommend_device())
        }