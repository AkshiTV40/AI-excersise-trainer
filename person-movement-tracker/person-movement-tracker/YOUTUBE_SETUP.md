# YouTube Analysis Feature - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt
```

New packages added:
- `yt-dlp` - Download videos from YouTube and 500+ platforms
- `requests` - HTTP client library

### 2. Start the Backend

```bash
# From the backend directory
python -m src.main

# Or
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the Frontend

```bash
# From the frontend directory
npm install
npm run dev
```

### 4. Access the Application

Open your browser to: `http://localhost:5173` (or the URL shown by Vite)

## How to Use

### Basic Steps

1. **Click "YouTube" Tab** - Switch to YouTube analysis mode
2. **Paste YouTube URL** - Enter a video URL (any length, but max 10 min analyzed)
3. **Select Exercise Type** - Choose the exercise to analyze
4. **Click "Analyze Video"** - Wait for results

### What Happens

1. **Download** (5-30s) - Video downloads to temporary storage
2. **Extract Frames** (2-10s) - Extracts frames from video
3. **Pose Detection** (1-5s per frame) - Detects person's pose
4. **Analysis** - Analyzes form and provides feedback
5. **Cleanup** - Temporary files are deleted

## Supported Platforms

✅ YouTube
✅ Vimeo  
✅ Dailymotion
✅ Instagram
✅ And 500+ more

## Example Videos to Try

### Squat Examples
- `https://www.youtube.com/watch?v=...` (Replace with actual squat video)

### Pushup Examples
- `https://www.youtube.com/watch?v=...` (Replace with actual pushup video)

## Expected Results

### Good Form (85-100%)
- Consistent movement
- Proper alignment
- No critical issues

### Decent Form (70-84%)
- Minor form deviations
- Some alignment issues
- Few warnings

### Needs Work (50-69%)
- Multiple form issues
- Poor alignment
- Multiple warnings

### Poor Form (<50%)
- Major form issues
- High injury risk
- Many critical issues

## Troubleshooting

### "Failed to download video"
- Check if URL is correct
- Verify internet connection
- Try a different video
- Some age-restricted videos can't download

### "No people detected"
- Ensure person is in frame
- Check lighting
- Ensure body is fully visible
- Move closer to camera

### Long processing time
- Longer videos take longer
- More frames = more processing
- Maximum 100 frames analyzed
- Typical time: 30-60 seconds

### API Connection Error
```bash
# Check backend is running
# Terminal 1:
cd backend
python -m src.main

# Terminal 2:
cd frontend
npm run dev
```

## Configuration

### Backend Settings (`backend/src/config.py`)

```python
# Maximum video duration (seconds)
MAX_VIDEO_DURATION = 600  # 10 minutes

# Frame sampling - analyze every Nth frame
FRAME_INTERVAL = 5  # Every 5th frame

# Maximum frames to analyze
MAX_FRAMES = 100

# Temporary storage
TEMP_DIR = tempfile.gettempdir()
```

### Frontend Settings (`frontend/src/components/YouTubeAnalyzer.jsx`)

```javascript
// Default exercise
const [selectedExercise, setSelectedExercise] = useState('squat');

// Update the numbers to customize display
```

## API Reference

### 1. Get Video Info
```bash
curl -X POST http://localhost:8000/api/youtube/video-info \
  -F "url=https://youtube.com/watch?v=..."
```

### 2. Analyze Video
```bash
curl -X POST http://localhost:8000/api/youtube/analyze \
  -F "url=https://youtube.com/watch?v=..." \
  -F "exercise_type=squat"
```

### 3. Get Supported Exercises
```bash
curl http://localhost:8000/api/youtube/supported-exercises
```

## Testing

### Run Tests
```bash
cd backend
python test_youtube_analysis.py

# Test with real video
python test_youtube_analysis.py --url "https://youtube.com/watch?v=..." --exercise squat
```

## Performance Tips

1. **Use shorter videos** - Under 5 minutes is ideal
2. **Good lighting** - Ensure person is well-lit
3. **Close-up views** - Person should fill most of the frame
4. **Stable camera** - Minimal camera shake
5. **Full body visible** - Entire body should be in frame

## System Requirements

### Minimum
- RAM: 4GB
- CPU: Modern dual-core processor
- GPU: Optional but recommended
- Internet: Required for video download

### Recommended
- RAM: 8GB+
- CPU: 4+ cores
- GPU: NVIDIA/AMD with CUDA/ROCm support
- Internet: High-speed (for faster downloads)

## File Organization

```
person-movement-tracker/
├── backend/
│   ├── src/
│   │   ├── services/
│   │   │   ├── youtube_service.py    (NEW)
│   │   │   ├── video_analysis_service.py  (NEW)
│   │   │   └── ...
│   │   ├── api/
│   │   │   ├── routes.py              (MODIFIED)
│   │   │   └── youtube_routes.py      (NEW)
│   │   └── ...
│   ├── test_youtube_analysis.py      (NEW)
│   ├── requirements.txt               (MODIFIED)
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── YouTubeAnalyzer.jsx   (NEW)
│   │   │   └── ...
│   │   ├── App.jsx                   (MODIFIED)
│   │   └── ...
│   └── ...
└── docs/
    ├── YOUTUBE_ANALYSIS.md           (NEW)
    └── ...
```

## Features

✅ YouTube video downloading
✅ Frame extraction and analysis
✅ Multiple exercise types
✅ Real-time form feedback
✅ Issue detection with severity
✅ Detailed recommendations
✅ Form scoring system
✅ Video info preview
✅ Automatic cleanup
✅ Progress tracking

## Future Enhancements

- [ ] Batch video analysis
- [ ] Real-time streaming analysis
- [ ] Custom form rules
- [ ] Multi-person analysis
- [ ] Export analysis reports
- [ ] Video clip generation
- [ ] Comparison mode
- [ ] Mobile app support

## Support & Issues

If you encounter any issues:

1. **Check the logs** - Look at backend console output
2. **Verify setup** - Ensure all dependencies installed
3. **Test manually** - Use the test script
4. **Check internet** - Verify connection for YouTube access

## Next Steps

1. Review the full [YOUTUBE_ANALYSIS.md](./docs/YOUTUBE_ANALYSIS.md) documentation
2. Try with different videos and exercises
3. Check the API endpoints in [API.md](./docs/API.md)
4. Explore customization options

## Contact

For issues or questions, refer to the main project documentation.

---

**Happy analyzing!** 🎥💪
