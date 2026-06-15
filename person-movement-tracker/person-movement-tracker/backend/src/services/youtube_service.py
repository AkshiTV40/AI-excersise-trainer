"""
YouTube Video Fetching and Processing Service
Handles downloading and processing YouTube videos for analysis
"""

import os
import tempfile
import asyncio
import logging
from typing import Optional, Dict, Tuple
import yt_dlp
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for fetching and processing YouTube videos"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize YouTube service
        
        Args:
            temp_dir: Temporary directory for video storage
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.downloaded_videos = {}
        
    async def fetch_video(self, url: str, max_duration: int = 600) -> Tuple[bool, str, Optional[str]]:
        """
        Fetch YouTube video and save locally
        
        Args:
            url: YouTube URL
            max_duration: Maximum video duration in seconds (default 10 minutes)
            
        Returns:
            Tuple of (success, file_path, error_message)
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._download_video, 
                url, 
                max_duration
            )
            return result
        except Exception as e:
            error_msg = f"Failed to fetch video: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def _download_video(self, url: str, max_duration: int) -> Tuple[bool, str, Optional[str]]:
        """
        Internal method to download video (runs in executor)
        
        Args:
            url: YouTube URL
            max_duration: Maximum duration in seconds
            
        Returns:
            Tuple of (success, file_path, error_message)
        """
        try:
            # Create unique filename with timestamp
            import time
            timestamp = int(time.time() * 1000)
            output_path = os.path.join(self.temp_dir, f"youtube_{timestamp}.mp4")
            
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': output_path[:-4],  # Remove .mp4 extension
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading video from: {url}")
                info = ydl.extract_info(url, download=True)
                duration = info.get('duration', 0)
                
                # Check duration
                if duration > max_duration:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    return False, "", f"Video duration ({duration}s) exceeds maximum ({max_duration}s)"
                
                # Find the actual file (yt-dlp might add extension)
                if not os.path.exists(output_path):
                    # Try with .mp4 extension
                    if os.path.exists(output_path + '.mp4'):
                        output_path = output_path + '.mp4'
                    else:
                        # Find any file matching the pattern
                        import glob
                        pattern = output_path.replace('.mp4', '') + '*'
                        matches = glob.glob(pattern)
                        if matches:
                            output_path = matches[0]
                        else:
                            return False, "", "Downloaded file not found"
                
                self.downloaded_videos[url] = output_path
                logger.info(f"Video downloaded successfully: {output_path}")
                return True, output_path, None
                
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return False, "", str(e)
    
    async def get_video_info(self, url: str) -> Dict:
        """
        Get information about YouTube video without downloading
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with video information
        """
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, self._extract_info, url)
            return info
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_info(self, url: str) -> Dict:
        """
        Extract video information without downloading
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with video info
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    "success": True,
                    "title": info.get('title', ''),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', ''),
                    "upload_date": info.get('upload_date', ''),
                    "description": info.get('description', '')[:200],  # First 200 chars
                    "thumbnail": info.get('thumbnail', '')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_frames(self, video_path: str, frame_interval: int = 5) -> Tuple[bool, list, Optional[str]]:
        """
        Extract frames from video at specified interval
        
        Args:
            video_path: Path to video file
            frame_interval: Extract every Nth frame
            
        Returns:
            Tuple of (success, list_of_frame_arrays, error_message)
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._extract_frames_sync,
                video_path,
                frame_interval
            )
            return result
        except Exception as e:
            error_msg = f"Failed to extract frames: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg
    
    def _extract_frames_sync(self, video_path: str, frame_interval: int) -> Tuple[bool, list, Optional[str]]:
        """
        Synchronously extract frames from video
        
        Args:
            video_path: Path to video file
            frame_interval: Extract every Nth frame
            
        Returns:
            Tuple of (success, list_of_frame_arrays, error_message)
        """
        try:
            if not os.path.exists(video_path):
                return False, [], f"Video file not found: {video_path}"
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, [], "Could not open video file"
            
            frames = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    # Resize to reduce memory usage
                    frame = cv2.resize(frame, (640, 480))
                    frames.append(frame)
                
                frame_count += 1
                
                # Limit to reasonable number of frames for analysis
                if len(frames) >= 100:  # Max 100 frames
                    break
            
            cap.release()
            
            if not frames:
                return False, [], "No frames extracted from video"
            
            logger.info(f"Extracted {len(frames)} frames from video")
            return True, frames, None
            
        except Exception as e:
            logger.error(f"Frame extraction error: {str(e)}")
            return False, [], str(e)
    
    def cleanup_video(self, video_path: str) -> bool:
        """
        Delete downloaded video file to save space
        
        Args:
            video_path: Path to video file
            
        Returns:
            Success status
        """
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up video: {video_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup video: {str(e)}")
            return False
    
    def cleanup_all(self) -> None:
        """Clean up all downloaded videos"""
        for url, video_path in self.downloaded_videos.items():
            self.cleanup_video(video_path)
        self.downloaded_videos.clear()
