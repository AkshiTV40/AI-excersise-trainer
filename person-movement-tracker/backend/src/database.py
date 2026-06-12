import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

# Database file path
DB_PATH = Path(__file__).parent.parent / "data" / "videos.db"

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Create videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exercise_type TEXT,
                file_size INTEGER,
                duration REAL,
                width INTEGER,
                height INTEGER,
                description TEXT
            )
        ''')
        conn.commit()
    finally:
        conn.close()

def add_video(filename: str, original_filename: str, exercise_type: Optional[str] = None, 
              file_size: Optional[int] = None, duration: Optional[float] = None,
              width: Optional[int] = None, height: Optional[int] = None,
              description: Optional[str] = None) -> int:
    """Add a video record to the database and return the ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO videos (filename, original_filename, exercise_type, upload_date, 
                                file_size, duration, width, height, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filename, original_filename, exercise_type, datetime.now(), 
              file_size, duration, width, height, description))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_video(video_id: int) -> Optional[dict]:
    """Get a video record by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def get_videos(limit: int = 100, offset: int = 0) -> List[dict]:
    """Get a list of videos with pagination."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM videos 
            ORDER BY upload_date DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def delete_video(video_id: int) -> bool:
    """Delete a video record by ID. Returns True if deleted."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()