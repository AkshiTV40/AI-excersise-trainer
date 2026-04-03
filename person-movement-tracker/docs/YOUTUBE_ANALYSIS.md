# YouTube Video Analysis Feature

## Overview

The Person Movement Tracker now supports analyzing YouTube videos to detect and evaluate exercise form. This feature allows you to fetch videos from YouTube and perform frame-by-frame analysis to identify exercise form issues and provide recommendations.

## Features

### 1. **YouTube Video Fetching**
- Fetch videos from YouTube and other supported platforms
- Automatic video information extraction (title, duration, uploader, thumbnail)
- Configurable maximum video duration (default: 10 minutes)

### 2. **Frame Extraction & Analysis**
- Intelligent frame sampling to reduce processing time
- Pose detection using MediaPipe
- Exercise-specific form analysis
- Frame-by-frame feedback with form scores

### 3. **Exercise Type Support**
The system supports the following exercises:
- **Squat** - Form check for knee alignment and depth
- **Pushup** - Form check for body alignment and elbow position
- **Lunge** - Form check for knee and hip alignment
- **Plank** - Form check for body alignment and hip position
- **Deadlift** - Form check for back alignment and lift mechanics
- **Bench Press** - Form check for bar path and elbow position
- **Overhead Press** - Form check for core engagement and shoulder stability
- **Bicep Curl** - Form check for elbow position and arm movement
- **Tricep Extension** - Form check for arm alignment and range of motion
- **Jumping Jack** - Form check for coordination and body alignment

### 4. **Detailed Feedback**
- Overall form score (0-100%)
- Issue severity levels: Critical, Warning, Info
- Specific suggestions for form correction
- Frame-by-frame analysis with detailed recommendations

## Architecture

### Backend Components

#### YouTubeService (`backend/src/services/youtube_service.py`)
- **Fetch videos** from YouTube using `yt-dlp`
- **Extract frames** at configurable intervals
- **Manage temporary files** and cleanup
- Async/await support for non-blocking operations

#### VideoAnalysisService (`backend/src/services/video_analysis_service.py`)
- **Pose detection** using MediaPipe
- **Exercise-specific analysis** with form validation
- **Issue detection** with severity levels
- **Detailed reporting** and recommendations

#### API Routes (`backend/src/api/routes.py`)
New endpoints:
```
POST /api/youtube/video-info
POST /api/youtube/analyze
GET /api/youtube/supported-exercises
POST /api/youtube/analyze-stream
```

### Frontend Components

#### YouTubeAnalyzer (`frontend/src/components/YouTubeAnalyzer.jsx`)
- YouTube URL input
- Exercise type selector
- Real-time progress tracking
- Video info display
- Analysis results visualization
- Frame-by-frame detail view

## API Endpoints

### 1. Get Video Information
```
POST /api/youtube/video-info
Parameters:
  - url: str (YouTube URL)
  
Returns:
  {
    "success": bool,
    "title": str,
    "duration": int (seconds),
    "uploader": str,
    "upload_date": str,
    "description": str,
    "thumbnail": str
  }
```

### 2. Analyze Video
```
POST /api/youtube/analyze
Parameters:
  - url: str (YouTube URL)
  - exercise_type: str (optional, exercise to analyze for)
  
Returns:
  {
    "success": bool,
    "url": str,
    "exercise_type": str,
    "total_frames": int,
    "analyzed_frames": int,
    "duration": float,
    "fps": float,
    "summary": {
      "status": str,
      "overall_form_score": float,
      "frames_with_people": int,
      "total_frames": int,
      "critical_issues": int,
      "warnings": int,
      "info_messages": int,
      "exercise_type": str,
      "recommendations": [str]
    },
    "frame_analyses": [
      {
        "frame_number": int,
        "timestamp": float,
        "people_detected": int,
        "poses": [array],
        "issues": [array],
        "form_score": float
      }
    ]
  }
```

### 3. Get Supported Exercises
```
GET /api/youtube/supported-exercises

Returns:
  {
    "success": bool,
    "exercises": [
      {
        "type": str,
        "name": str,
        "description": str
      }
    ],
    "total": int
  }
```

## Installation & Setup

### Backend Requirements

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

Key new packages:
- `yt-dlp>=2024.1.1` - YouTube video downloading
- `requests>=2.31.0` - HTTP requests

2. **Environment setup**:
The YouTube feature requires internet access to:
- YouTube servers (for video fetching)
- Other supported video platforms

### Frontend Setup

The YouTube Analyzer component is already integrated into the main app. No additional installation needed.

## Usage

### Step 1: Navigate to YouTube Tab
In the application UI, click the **"YouTube"** tab in the mode selector.

### Step 2: Enter YouTube URL
Paste a YouTube video URL into the "YouTube Video URL" field.

Examples:
- `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- `https://youtu.be/dQw4w9WgXcQ`

### Step 3: Select Exercise Type
Choose the exercise type you want to analyze from the dropdown menu.

### Step 4: Get Video Info (Optional)
Click **"Get Video Info"** to preview video details before analysis.

### Step 5: Analyze Video
Click **"Analyze Video"** to start the analysis:
1. Video downloads (this may take a moment)
2. Frames are extracted
3. Pose detection runs on each frame
4. Exercise form analysis is performed
5. Results are displayed

### Step 6: Review Results

The analysis displays:
- **Form Score**: Overall form quality percentage
- **Summary Statistics**: Frames analyzed, issues found
- **Frame-by-Frame Analysis**: Detailed feedback per frame
- **Recommendations**: Specific suggestions for improvement

## Form Score Interpretation

- **85-100%**: EXCELLENT - Great form, continue as is
- **70-84%**: GOOD - Solid form with minor issues
- **50-69%**: NEEDS IMPROVEMENT - Address the identified issues
- **Below 50%**: POOR - Significant corrections needed

## Issue Severity Levels

### Critical (Red)
- Major form issues that risk injury
- Must be corrected immediately
- Examples: Hips sagging in plank, knees caving inward in squat

### Warning (Yellow)
- Notable form deviations
- Should be corrected for optimal form
- Examples: Slight knee deviation, minor posture issues

### Info (Blue)
- Minor suggestions
- Optional improvements
- Examples: Could go deeper, better engagement possible

## Error Handling

### Common Issues and Solutions

1. **"Failed to download video"**
   - Check YouTube URL is correct
   - Verify internet connection
   - Ensure video is public/accessible
   - Some age-restricted videos may not download

2. **"Failed to extract frames"**
   - Video codec may not be supported
   - Video file may be corrupted
   - Try with a different video

3. **"No people detected"**
   - Person may be too far from camera
   - Lighting may be too poor
   - Body may be partially obscured

4. **Long processing time**
   - Longer videos take more time
   - More frames = longer analysis
   - Max 100 frames analyzed per video

## Performance Considerations

### Processing Time
- Video fetching: ~5-30 seconds (depends on size)
- Frame extraction: ~2-10 seconds
- Pose detection: ~1-5 seconds per frame
- **Total**: Typically 30-60 seconds for full analysis

### Resource Usage
- RAM: ~500MB-2GB depending on video resolution
- Disk: Temporary storage for downloaded video (auto-cleaned)
- CPU: High usage during pose detection

### Optimization Tips
1. Use shorter videos for faster analysis
2. Lower resolution videos process faster
3. Ensure sufficient available RAM
4. Close other applications during analysis

## Advanced Configuration

### Backend Configuration (`backend/src/config.py`)

You can customize:
```python
# Maximum video duration (seconds)
MAX_VIDEO_DURATION = 600  # 10 minutes

# Frame sampling interval
FRAME_INTERVAL = 5  # Every 5th frame

# Maximum frames to analyze
MAX_FRAMES = 100

# Temporary directory for downloads
TEMP_DIR = tempfile.gettempdir()
```

### Frontend Customization

Edit `YouTubeAnalyzer.jsx`:
```javascript
// Modify default exercise type
const [selectedExercise, setSelectedExercise] = useState('pushup');

// Change progress update frequency
const PROGRESS_UPDATE_INTERVAL = 500; // milliseconds

// Customize display frames
const FRAMES_TO_DISPLAY = 20;
```

## Supported Video Platforms

The application uses `yt-dlp` which supports:
- ✅ YouTube
- ✅ Vimeo
- ✅ Dailymotion
- ✅ Instagram
- ✅ TikTok (with limitations)
- ✅ And 500+ other platforms

## Privacy & Security

- Videos are downloaded temporarily and automatically deleted after analysis
- No video data is stored or uploaded
- Processing happens locally on your machine
- Internet connection required only for video fetching

## Troubleshooting

### Debug Mode
Enable verbose logging:
```bash
# Backend
export DEBUG=True
python -m src.main

# Check logs for detailed error messages
```

### Test YouTube Analysis
Run the included test script:
```bash
cd backend
python test_youtube_analysis.py --url "https://youtube.com/watch?v=..." --exercise squat
```

## Future Enhancements

Planned features:
- [ ] Batch video analysis
- [ ] WebSocket streaming progress
- [ ] Comparison between multiple videos
- [ ] Exercise variation support
- [ ] Custom form rule definition
- [ ] Video clip generation with feedback overlays
- [ ] Multi-person analysis
- [ ] Real-time video stream analysis

## Support

For issues or questions:
1. Check the [main README](../README.md)
2. Review API documentation in [API.md](../docs/API.md)
3. Check existing issues on GitHub
4. Contact: [support email/link]

## License

See [LICENSE](../LICENSE) file for details.
