import json
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
import redis

try:
    from ..config import config
except ImportError:
    from config import config

@dataclass
class Session:
    session_id: str
    created_at: float
    last_activity: float
    frame_count: int
    total_inference_time: float
    track_history: Dict[int, List[dict]]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        return cls(**data)

class SessionManager:
    def __init__(self):
        self.redis_client = None
        self.local_sessions: Dict[str, Session] = {}
        self.session_timeout = 3600  # 1 hour
        
        # Try to connect to Redis
        try:
            self.redis_client = redis.from_url(config.redis_url)
            self.redis_client.ping()
            print("Connected to Redis")
        except Exception as e:
            print(f"Redis not available, using local storage: {e}")
            self.redis_client = None
    
    def create_session(self, session_id: str) -> Session:
        """Create a new session"""
        current_time = time.time()
        
        session = Session(
            session_id=session_id,
            created_at=current_time,
            last_activity=current_time,
            frame_count=0,
            total_inference_time=0.0,
            track_history={}
        )
        
        # Store session
        self._save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session = self._load_session(session_id)
        
        if session:
            # Check if session is expired
            if time.time() - session.last_activity > self.session_timeout:
                self.delete_session(session_id)
                return None
            
            # Update last activity
            session.last_activity = time.time()
            self._save_session(session)
        
        return session
    
    def update_session(self, session_id: str, **kwargs):
        """Update session data"""
        session = self.get_session(session_id)
        
        if not session:
            session = self.create_session(session_id)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.last_activity = time.time()
        self._save_session(session)
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if self.redis_client:
            self.redis_client.delete(f"session:{session_id}")
        else:
            if session_id in self.local_sessions:
                del self.local_sessions[session_id]
    
    def add_frame_result(self, session_id: str, inference_time: float, detections: list):
        """Add frame processing result to session"""
        session = self.get_session(session_id)
        
        if not session:
            session = self.create_session(session_id)
        
        session.frame_count += 1
        session.total_inference_time += inference_time
        
        # Update track history
        for det in detections:
            track_id = det.get('track_id')
            if track_id:
                if track_id not in session.track_history:
                    session.track_history[track_id] = []
                
                session.track_history[track_id].append({
                    'timestamp': time.time(),
                    'bbox': det.get('bbox'),
                    'confidence': det.get('confidence')
                })
        
        self._save_session(session)
    
    def get_session_stats(self, session_id: str) -> Optional[dict]:
        """Get session statistics"""
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        avg_inference_time = (session.total_inference_time / session.frame_count 
                             if session.frame_count > 0 else 0)
        
        return {
            'session_id': session_id,
            'created_at': session.created_at,
            'last_activity': session.last_activity,
            'frame_count': session.frame_count,
            'average_inference_time': avg_inference_time,
            'total_tracks': len(session.track_history),
            'active_tracks': len([t for t in session.track_history.values() 
                                 if t and time.time() - t[-1]['timestamp'] < 30])
        }
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = time.time()
        
        if self.redis_client:
            # Redis handles expiration automatically
            pass
        else:
            expired = []
            for session_id, session in self.local_sessions.items():
                if current_time - session.last_activity > self.session_timeout:
                    expired.append(session_id)
            
            for session_id in expired:
                del self.local_sessions[session_id]
    
    def _save_session(self, session: Session):
        """Save session to storage"""
        if self.redis_client:
            # Save to Redis with expiration
            self.redis_client.setex(
                f"session:{session.session_id}",
                self.session_timeout,
                json.dumps(session.to_dict())
            )
        else:
            # Save to local storage
            self.local_sessions[session.session_id] = session
    
    def _load_session(self, session_id: str) -> Optional[Session]:
        """Load session from storage"""
        if self.redis_client:
            data = self.redis_client.get(f"session:{session_id}")
            if data:
                return Session.from_dict(json.loads(data))
            return None
        else:
            return self.local_sessions.get(session_id)