import sqlite3
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Database file path
DB_PATH = Path(__file__).parent.parent / "data" / "videos.db"

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_column_exists(cursor, table_name: str, column_name: str, column_definition: str) -> None:
    cursor.execute(f'PRAGMA table_info({table_name})')
    existing_columns = {row[1] for row in cursor.fetchall()}
    if column_name not in existing_columns:
        cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}')


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
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

        _ensure_column_exists(cursor, 'videos', 'source', "TEXT DEFAULT 'upload'")
        _ensure_column_exists(cursor, 'videos', 'session_id', 'TEXT')
        _ensure_column_exists(cursor, 'videos', 'analysis_status', "TEXT DEFAULT 'pending'")
        _ensure_column_exists(cursor, 'videos', 'analysis_result_json', 'TEXT')
        _ensure_column_exists(cursor, 'videos', 'reference_video_id', 'INTEGER')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_exercise_type ON videos(exercise_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_source ON videos(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_session_id ON videos(session_id)')
        conn.commit()
    finally:
        conn.close()

def add_video(filename: str, original_filename: str, exercise_type: Optional[str] = None,
              file_size: Optional[int] = None, duration: Optional[float] = None,
              width: Optional[int] = None, height: Optional[int] = None,
              description: Optional[str] = None, source: Optional[str] = None,
              session_id: Optional[str] = None, analysis_status: Optional[str] = None,
              analysis_result_json: Optional[str] = None,
              reference_video_id: Optional[int] = None) -> int:
    """Add a video record to the database and return the ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO videos (filename, original_filename, exercise_type, upload_date,
                                file_size, duration, width, height, description, source,
                                session_id, analysis_status, analysis_result_json,
                                reference_video_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filename, original_filename, exercise_type, datetime.now(),
              file_size, duration, width, height, description, source, session_id,
              analysis_status, analysis_result_json, reference_video_id))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def update_video_analysis(video_id: int, analysis_status: str, analysis_result_json: Optional[str] = None) -> bool:
    """Update analysis status and optional JSON result for a video."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE videos
            SET analysis_status = ?, analysis_result_json = COALESCE(?, analysis_result_json)
            WHERE id = ?
        ''', (analysis_status, analysis_result_json, video_id))
        conn.commit()
        return cursor.rowcount > 0
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
