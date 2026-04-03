# YouTube Analysis API - Quick Reference

## Endpoints Summary

### 1. Get Video Information
Retrieve metadata about a YouTube video without downloading it.

```http
POST /api/youtube/video-info
Content-Type: application/x-www-form-urlencoded

url=https://www.youtube.com/watch?v=...
```

**Response:**
```json
{
  "success": true,
  "title": "Video Title",
  "duration": 300,
  "uploader": "Channel Name",
  "upload_date": "20240208",
  "description": "Video description...",
  "thumbnail": "https://..."
}
```

### 2. Analyze YouTube Video
Download a YouTube video and analyze exercise form.

```http
POST /api/youtube/analyze
Content-Type: application/x-www-form-urlencoded

url=https://www.youtube.com/watch?v=...
exercise_type=squat
```

**Response:**
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=...",
  "exercise_type": "squat",
  "total_frames": 150,
  "analyzed_frames": 30,
  "duration": 5.0,
  "fps": 30.0,
  "summary": {
    "status": "GOOD",
    "overall_form_score": 78.5,
    "frames_with_people": 25,
    "total_frames": 30,
    "critical_issues": 0,
    "warnings": 3,
    "info_messages": 5,
    "exercise_type": "squat",
    "recommendations": [
      "Good form! Keep practicing to maintain consistency",
      "Watch the knee alignment - slight deviation noticed"
    ]
  },
  "frame_analyses": [
    {
      "frame_number": 0,
      "timestamp": 0.0,
      "people_detected": 1,
      "poses": [
        {
          "landmarks": [
            {"x": 0.5, "y": 0.3, "z": 0.1, "visibility": 0.95},
            ...
          ],
          "confidence": 0.9
        }
      ],
      "issues": [
        {
          "severity": "info",
          "message": "Good squat depth",
          "suggestion": "Maintain this depth for optimal form"
        }
      ],
      "form_score": 85.0,
      "exercise_type": "squat"
    },
    ...
  ]
}
```

### 3. Get Supported Exercises
List all exercise types supported by the analyzer.

```http
GET /api/youtube/supported-exercises
```

**Response:**
```json
{
  "success": true,
  "exercises": [
    {
      "type": "squat",
      "name": "Squat",
      "description": "Lower body exercise - form check for knee alignment and depth"
    },
    {
      "type": "pushup",
      "name": "Pushup",
      "description": "Upper body exercise - form check for body alignment and elbow position"
    },
    {
      "type": "lunge",
      "name": "Lunge",
      "description": "Lower body exercise - form check for knee and hip alignment"
    },
    {
      "type": "plank",
      "name": "Plank",
      "description": "Core exercise - form check for body alignment and hip position"
    },
    {
      "type": "deadlift",
      "name": "Deadlift",
      "description": "Lower body compound - form check for back alignment and lift mechanics"
    },
    {
      "type": "bench_press",
      "name": "Bench Press",
      "description": "Upper body compound - form check for bar path and elbow position"
    },
    {
      "type": "overhead_press",
      "name": "Overhead Press",
      "description": "Upper body exercise - form check for core engagement and shoulder stability"
    },
    {
      "type": "bicep_curl",
      "name": "Bicep Curl",
      "description": "Upper body isolation - form check for elbow position and arm movement"
    },
    {
      "type": "tricep_extension",
      "name": "Tricep Extension",
      "description": "Upper body isolation - form check for arm alignment and range of motion"
    },
    {
      "type": "jumping_jack",
      "name": "Jumping Jack",
      "description": "Cardio exercise - form check for coordination and body alignment"
    }
  ],
  "total": 10
}
```

## HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Analysis completed successfully |
| 400 | Bad Request | Invalid exercise type or missing URL |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Server Error | Processing failed, video unavailable |

## Error Responses

### Invalid URL
```json
{
  "detail": "URL is required"
}
```

### Unsupported Exercise
```json
{
  "detail": "Invalid exercise type. Valid types: squat, pushup, lunge, ..."
}
```

### Download Failed
```json
{
  "detail": "Failed to download video: Video is age-restricted"
}
```

### Video Processing Failed
```json
{
  "detail": "Analysis failed: No people detected in video"
}
```

## cURL Examples

### Get Video Info
```bash
curl -X POST http://localhost:8000/api/youtube/video-info \
  -d "url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Analyze Squat Video
```bash
curl -X POST http://localhost:8000/api/youtube/analyze \
  -d "url=https://www.youtube.com/watch?v=..." \
  -d "exercise_type=squat"
```

### Get Supported Exercises
```bash
curl http://localhost:8000/api/youtube/supported-exercises
```

## Python Examples

### Using requests library
```python
import requests

# Get video info
response = requests.post(
    'http://localhost:8000/api/youtube/video-info',
    data={'url': 'https://www.youtube.com/watch?v=...'}
)
info = response.json()
print(f"Title: {info['title']}")
print(f"Duration: {info['duration']}s")

# Analyze video
response = requests.post(
    'http://localhost:8000/api/youtube/analyze',
    data={
        'url': 'https://www.youtube.com/watch?v=...',
        'exercise_type': 'squat'
    },
    timeout=300
)
result = response.json()
print(f"Form Score: {result['summary']['overall_form_score']}%")
```

### Using fetch (JavaScript)
```javascript
// Get video info
const response = await fetch('/api/youtube/video-info', {
  method: 'POST',
  body: new FormData(Object.entries({
    url: 'https://www.youtube.com/watch?v=...'
  }))
});
const info = await response.json();

// Analyze video
const formData = new FormData();
formData.append('url', 'https://www.youtube.com/watch?v=...');
formData.append('exercise_type', 'squat');

const response = await fetch('/api/youtube/analyze', {
  method: 'POST',
  body: formData
});
const result = await response.json();
```

## Response Time Expectations

| Operation | Time |
|-----------|------|
| Get video info | 2-5 seconds |
| Download video | 5-30 seconds |
| Extract frames | 2-10 seconds |
| Analyze frames | 5-60 seconds |
| **Total** | **15-105 seconds** |

## Rate Limiting

Currently no rate limiting. In production, consider:
- Limit requests per IP
- Queue long-running analyses
- Cache video info responses
- Set timeouts for operations

## Form Score Scale

```
85-100% ┌─────────────┐  EXCELLENT
        │ Great form! │  - Keep it up
        │             │  - Minimal issues
70-84%  ├─────────────┤  GOOD
        │ Solid form  │  - Minor adjustments
        │             │  - Few issues
50-69%  ├─────────────┤  NEEDS IMPROVEMENT
        │ Work needed │  - Multiple issues
        │             │  - Clear corrections required
0-49%   ├─────────────┤  POOR
        │ Major fixes │  - Significant form issues
        │             │  - Risk of injury
        └─────────────┘
```

## Issue Severity

| Severity | Color | Priority | Example |
|----------|-------|----------|---------|
| Critical | 🔴 Red | Immediate | Hips sagging in plank |
| Warning | 🟡 Yellow | High | Knee deviation |
| Info | 🔵 Blue | Low | Could go deeper |

## Pose Landmarks (33 total)

```
Head Region:
  0: Nose
  1: Left Eye
  2: Right Eye
  3: Left Ear
  4: Right Ear

Body:
  5: Left Shoulder
  6: Right Shoulder
  7: Left Elbow
  8: Right Elbow
  9: Left Wrist
  10: Right Wrist

Core:
  11: Left Hip
  12: Right Hip
  13: Left Knee
  14: Right Knee
  15: Left Ankle
  16: Right Ankle

Additional:
  17-23: Hand landmarks (left)
  24-32: Hand landmarks (right)
```

## Troubleshooting Common Issues

### 400: Invalid Exercise Type
**Solution:** Check the list with `/api/youtube/supported-exercises`

### 500: Failed to Download
**Solution:** Check YouTube URL is public and accessible

### 500: No People Detected
**Solution:** Ensure person is fully visible in video

### Slow Response Time
**Solution:** 
- Use shorter videos
- Check system resources
- Try simpler exercises first

## Best Practices

1. **Validate exercise type** before sending
2. **Use form data** for file uploads
3. **Set appropriate timeouts** (300+ seconds)
4. **Check response status** before parsing
5. **Handle errors gracefully**
6. **Cache supported exercises** list
7. **Clean up** temporary files

## Integration Checklist

- [ ] Backend running on localhost:8000
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Network access to YouTube
- [ ] Sufficient RAM (4GB+)
- [ ] Python 3.8+ installed
- [ ] MediaPipe working
- [ ] OpenCV working

## Environment Variables

```bash
# Backend configuration
export API_HOST=0.0.0.0
export API_PORT=8000
export DEBUG=False

# CORS settings
export CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# YouTube settings
export YOUTUBE_MAX_DURATION=600  # seconds
export YOUTUBE_FRAME_INTERVAL=5  # every Nth frame
```

---

**Ready to integrate? Start with the `/api/youtube/supported-exercises` endpoint!**
