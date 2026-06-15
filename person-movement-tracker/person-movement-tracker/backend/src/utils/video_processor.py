import cv2
import numpy as np
from typing import Iterator, Tuple, Optional, Callable
from dataclasses import dataclass
import time

@dataclass
class VideoInfo:
    width: int
    height: int
    fps: float
    total_frames: int
    duration: float
    codec: str

class VideoProcessor:
    def __init__(self, source: str or int):
        self.source = source
        self.cap = None
        self.info = None
        
    def open(self) -> bool:
        """Open video source"""
        self.cap = cv2.VideoCapture(self.source)
        
        if not self.cap.isOpened():
            return False
        
        # Get video info
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        # Get codec
        fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        
        self.info = VideoInfo(
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration=duration,
            codec=codec
        )
        
        return True
    
    def close(self):
        """Close video source"""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def frames(self) -> Iterator[np.ndarray]:
        """Iterate through video frames"""
        if not self.cap:
            raise ValueError("Video not opened. Call open() first.")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame
    
    def get_frame(self, frame_number: int) -> Optional[np.ndarray]:
        """Get specific frame by number"""
        if not self.cap:
            return None
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        
        return frame if ret else None
    
    def get_frame_at_time(self, seconds: float) -> Optional[np.ndarray]:
        """Get frame at specific time (seconds)"""
        if not self.cap or self.info.fps <= 0:
            return None
        
        frame_number = int(seconds * self.info.fps)
        return self.get_frame(frame_number)
    
    def process_video(self, 
                     processor: Callable[[np.ndarray], np.ndarray],
                     output_path: str,
                     fps: Optional[float] = None) -> bool:
        """Process video with custom function and save output"""
        if not self.cap:
            return False
        
        # Use original fps if not specified
        output_fps = fps or self.info.fps
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            output_path,
            fourcc,
            output_fps,
            (self.info.width, self.info.height)
        )
        
        if not out.isOpened():
            return False
        
        try:
            for frame in self.frames():
                processed_frame = processor(frame)
                out.write(processed_frame)
            
            return True
        finally:
            out.release()
    
    def extract_frames(self, 
                      output_pattern: str,
                      interval: int = 1,
                      max_frames: Optional[int] = None) -> int:
        """Extract frames as images"""
        if not self.cap:
            return 0
        
        count = 0
        frame_count = 0
        
        for frame in self.frames():
            if frame_count % interval == 0:
                output_path = output_pattern.format(count)
                cv2.imwrite(output_path, frame)
                count += 1
                
                if max_frames and count >= max_frames:
                    break
            
            frame_count += 1
        
        return count
    
    def get_video_info(self) -> VideoInfo:
        """Get video information"""
        return self.info

class VideoStream:
    """Real-time video stream processor"""
    
    def __init__(self, source: str or int = 0):
        self.source = source
        self.cap = None
        self.is_running = False
        self.frame_callback = None
        self.process_callback = None
    
    def start(self, 
             frame_callback: Optional[Callable] = None,
             process_callback: Optional[Callable] = None) -> bool:
        """Start video stream"""
        self.cap = cv2.VideoCapture(self.source)
        
        if not self.cap.isOpened():
            return False
        
        self.is_running = True
        self.frame_callback = frame_callback
        self.process_callback = process_callback
        
        return True
    
    def stop(self):
        """Stop video stream"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def run(self):
        """Run video stream loop"""
        if not self.cap:
            raise ValueError("Stream not started. Call start() first.")
        
        while self.is_running:
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            # Process frame if callback provided
            if self.process_callback:
                frame = self.process_callback(frame)
            
            # Send frame to callback
            if self.frame_callback:
                self.frame_callback(frame)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get single frame from stream"""
        if not self.cap:
            return None
        
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def set_resolution(self, width: int, height: int):
        """Set camera resolution"""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    def set_fps(self, fps: float):
        """Set camera FPS"""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FPS, fps)