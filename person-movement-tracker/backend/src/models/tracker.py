from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass
from collections import defaultdict
import time

from deep_sort_realtime.deepsort_tracker import DeepSort

try:
    from .base_detector import Detection
except ImportError:
    from models.base_detector import Detection

@dataclass
class Track:
    track_id: int
    detections: List[Detection]
    start_time: float
    last_update: float
    color: tuple
    
    @property
    def current_position(self) -> Optional[Detection]:
        if self.detections:
            return self.detections[-1]
        return None
    
    @property
    def path(self) -> List[List[float]]:
        return [det.bbox for det in self.detections]
    
    @property
    def speed(self) -> float:
        if len(self.detections) < 2:
            return 0.0
        
        # Calculate average speed in pixels per second
        total_distance = 0
        total_time = 0
        
        for i in range(1, len(self.detections)):
            prev = self.detections[i-1]
            curr = self.detections[i]
            
            # Calculate center points
            prev_center = [(prev.bbox[0] + prev.bbox[2]) / 2, 
                          (prev.bbox[1] + prev.bbox[3]) / 2]
            curr_center = [(curr.bbox[0] + curr.bbox[2]) / 2, 
                          (curr.bbox[1] + curr.bbox[3]) / 2]
            
            # Euclidean distance
            distance = np.sqrt((curr_center[0] - prev_center[0])**2 + 
                             (curr_center[1] - prev_center[1])**2)
            
            time_diff = curr.timestamp - prev.timestamp if hasattr(curr, 'timestamp') else 0.1
            
            total_distance += distance
            total_time += time_diff
        
        return total_distance / total_time if total_time > 0 else 0.0

class MultiObjectTracker:
    def __init__(self, tracker_type: str = "deepsort", **kwargs):
        self.tracker_type = tracker_type
        self.tracks: Dict[int, Track] = {}
        self.next_track_id = 0
        self.colors = self._generate_colors()
        
        # Initialize DeepSORT tracker
        if tracker_type == "deepsort":
            self.tracker = DeepSort(
                max_age=kwargs.get('max_age', 30),
                n_init=kwargs.get('n_init', 3),
                nn_budget=kwargs.get('nn_budget', 100),
                max_iou_distance=kwargs.get('max_iou_distance', 0.7),
                max_cosine_distance=kwargs.get('max_cosine_distance', 0.2)
            )
        else:
            self.tracker = None
    
    def update(self, detections: List[Detection], frame: np.ndarray) -> List[Detection]:
        """Update tracks with new detections"""
        current_time = time.time()
        
        if self.tracker_type == "deepsort" and self.tracker:
            # Convert detections to DeepSORT format
            ds_detections = []
            for det in detections:
                bbox = det.bbox
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                
                ds_detections.append(([bbox[0], bbox[1], width, height], 
                                     det.confidence, 
                                     det.class_name))
            
            # Update tracker
            tracks = self.tracker.update_tracks(ds_detections, frame=frame)
            
            # Update our track records
            updated_detections = []
            for track in tracks:
                if not track.is_confirmed():
                    continue
                
                track_id = track.track_id
                ltrb = track.to_ltrb()
                
                # Create detection with track ID
                det = Detection(
                    bbox=list(ltrb),
                    confidence=track.get_det_conf() if hasattr(track, 'get_det_conf') else 0.5,
                    class_id=0,  # Person class
                    class_name='person',
                    track_id=track_id
                )
                
                # Update track history
                if track_id not in self.tracks:
                    self.tracks[track_id] = Track(
                        track_id=track_id,
                        detections=[],
                        start_time=current_time,
                        last_update=current_time,
                        color=self.colors[track_id % len(self.colors)]
                    )
                
                # Add timestamp
                det.timestamp = current_time
                self.tracks[track_id].detections.append(det)
                self.tracks[track_id].last_update = current_time
                
                # Limit track history
                if len(self.tracks[track_id].detections) > 100:
                    self.tracks[track_id].detections.pop(0)
                
                updated_detections.append(det)
            
            # Clean old tracks
            self._cleanup_tracks(current_time)
            
            return updated_detections
        
        return detections
    
    def _cleanup_tracks(self, current_time: float, max_age: float = 30.0):
        """Remove tracks that haven't been updated"""
        to_remove = []
        for track_id, track in self.tracks.items():
            if current_time - track.last_update > max_age:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            del self.tracks[track_id]
    
    def _generate_colors(self, n_colors: int = 100):
        """Generate distinct colors for tracks"""
        import colorsys
        colors = []
        for i in range(n_colors):
            hue = i / n_colors
            lightness = 0.5
            saturation = 0.8
            rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
            colors.append(tuple(int(c * 255) for c in rgb))
        return colors
    
    def get_track_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for all active tracks"""
        stats = {}
        for track_id, track in self.tracks.items():
            stats[track_id] = {
                'age': time.time() - track.start_time,
                'detection_count': len(track.detections),
                'speed': track.speed,
                'color': track.color
            }
        return stats