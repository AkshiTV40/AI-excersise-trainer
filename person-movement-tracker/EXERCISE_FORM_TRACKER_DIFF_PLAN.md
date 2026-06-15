# Exercise Form Tracker (Video-based) — Live Capture, SQLite3 Storage, and Reference Comparison

## Goal

Create a form tracker that works on **live camera recordings**, uploaded user videos, and reference videos. The system should:

1. Capture a live exercise session from the browser camera.
2. Save the captured live video as an MP4 file.
3. Store captured video metadata in a **SQLite3** database.
4. Analyze the saved live/user video with pose estimation.
5. Compare the live/user video against a reference video and compute form deltas.

Core outputs:

- Saved live recording file
- SQLite3 video/session record
- Per-frame / per-rep pose metrics
- Aggregated delta features between live/user and reference
- Visual overlays or debug artifacts when needed

> Note: “Light videos can’t generate a skeleton” usually means **pose detection confidence is too low** or **frame sampling is too sparse**. The live capture path should preserve the original recording first, then run offline pose extraction with stronger confidence/fallback handling.

---

## Current repo live-capture path

The project already has the main live recording pieces:

### Frontend

- `frontend/src/components/RecordSession.jsx`
  - Opens camera with `navigator.mediaDevices.getUserMedia`.
  - Shows a live `<video>` preview.
  - Captures frames to a hidden `<canvas>`.
  - Sends JPEG data URLs during recording.
  - Displays the returned `sessionComplete.video_url`.

- `frontend/src/hooks/useRecordSession.js`
  - Connects to WebSocket endpoint `/ws/record-session`.
  - Sends config:
    - `exercise_type`
    - `duration_seconds`
  - Sends frame data:
    - `{ image: dataUrl }`
  - Exposes session status:
    - `idle`
    - `recording`
    - `processing`
    - `complete`
    - `error`

### Backend

- `backend/src/api/routes.py`
  - WebSocket endpoint: `/ws/record-session`
  - Helper: `_process_recorded_video(...)`
  - Saves captured frames to:
    - `backend/data/videos/recordings/`
  - Writes MP4 with `cv2.VideoWriter`.
  - Stores video metadata in SQLite3 using `add_video(...)`.
  - Returns:
    - `video_id`
    - `video_url`
    - `exercise_type`
    - `duration`
    - `frames_processed`
    - analysis summary and feedback

- `backend/src/database.py`
  - SQLite3 database:
    - `backend/data/videos.db`
  - Existing table:
    - `videos`
  - Existing helpers:
    - `init_db()`
    - `add_video(...)`
    - `get_video(video_id)`
    - `get_videos(...)`
    - `delete_video(video_id)`

### Analysis service

- `backend/src/services/exercise_form_tracker.py`
  - Video-based exercise form comparison service.
  - Uses OpenCV, YOLOv8 pose, smoothing, DTW alignment, and delta metrics.
  - Designed to compare:
    - reference video
    - live/user recorded video

---

## Target live video capture flow

### Step 1 — Configure live session

Frontend sends WebSocket config:

```json
{
  "config": {
    "exercise_type": "squat",
    "duration_seconds": 15
  }
}
```

Backend validates `exercise_type` against `ExerciseType`.

Expected backend response:

```json
{
  "type": "config_ack",
  "message": "Recording configured for squat for 15 seconds",
  "exercise_type": "squat",
  "duration_seconds": 15
}
```

---

### Step 2 — Capture live camera frames

Frontend flow:

1. Request camera permission.
2. Start live preview.
3. While recording, capture frames from the `<video>` element to a `<canvas>`.
4. Convert each canvas frame to JPEG data URL.
5. Send each frame over WebSocket.

Current capture interval:

- Every `100ms`, approximately `10 FPS`.

Recommended live-capture quality knobs:

- Keep `100ms` for lightweight capture.
- Use `66ms` for approximately `15 FPS`.
- Use `33ms` for approximately `30 FPS` only if bandwidth/backend can handle it.
- Prefer stable camera placement over high FPS for form tracking.

---

### Step 3 — Decode frames on backend

Backend WebSocket flow:

1. Receive `{ image: dataUrl }`.
2. Strip `data:image/...;base64,` prefix if present.
3. Decode base64 bytes.
4. Convert bytes to NumPy frame with OpenCV.
5. Validate frame decode.
6. Append decoded frame to the active session frame list.

If decoding fails, return:

```json
{
  "type": "error",
  "message": "Failed to decode image"
}
```

---

### Step 4 — Optional live skeleton overlay

During live capture, backend can run pose detection on each received frame and draw a skeleton before appending the frame.

Current backend path:

- `YOLOPoseDetector`
- `draw_yolo_17_skeleton(...)`

Important distinction:

- Live overlay is useful for user feedback.
- Offline analysis should re-run pose extraction from the saved video so it can use:
  - better sampling
  - smoothing
  - fallback frames
  - DTW alignment
  - reference comparison

---

### Step 5 — Stop recording

Recording can stop in two ways:

1. Automatic stop after `duration_seconds`.
2. Client sends:

```json
{
  "command": "stop"
}
```

Backend should respond with:

```json
{
  "type": "recording_stopped",
  "message": "Recording stopped after 12.4 seconds",
  "frames_captured": 124
}
```

Then backend processes the captured frames.

---

### Step 6 — Save captured live video to disk

Backend writes the live session to MP4:

- Directory:
  - `backend/data/videos/recordings/`
- Filename pattern:
  - `session_ws_record_<client_host>_<timestamp>.mp4`
- Encoder:
  - `mp4v`
- Writer:
  - `cv2.VideoWriter`

Recommended filename improvements:

- Include `exercise_type`.
- Include UTC timestamp.
- Avoid spaces.
- Keep extension `.mp4`.

Example:

```text
session_ws_record_127.0.0.1_squat_1718312345.mp4
```

---

## SQLite3 persistence model

### Recommended storage strategy

Use SQLite3 for **metadata and retrieval**, not raw video BLOBs.

Recommended approach:

1. Store the actual video file on disk under:
   - `backend/data/videos/recordings/`
2. Store metadata in SQLite3 table `videos`.
3. Serve the video through:
   - `GET /api/videos/{video_id}`

Why this is better than storing video BLOBs:

- Faster video serving.
- Smaller SQLite database.
- Easier backup/restore.
- Avoids loading large binary blobs into memory.
- Matches the current FastAPI route design.

Optional future mode:

- Add a `storage_strategy` column:
  - `filesystem`
  - `sqlite_blob`
- Add a `video_blob BLOB` column only if local-only offline storage is required.

---

## Existing SQLite3 schema

Current `backend/src/database.py` table:

```sql
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
```

For live capture, `add_video(...)` currently stores:

```python
video_id = add_video(
    filename=filename,
    original_filename=f"exercise_session_{exercise_type}_{timestamp}.mp4",
    exercise_type=exercise_type,
    file_size=os.path.getsize(video_path),
    duration=len(frames) / fps if fps > 0 else None,
    width=width,
    height=height,
    description=f"Recorded session for {exercise_type}"
)
```

---

## Recommended SQLite3 schema additions

To make live capture easier to query and debug, add these columns when schema evolution is allowed:

```sql
ALTER TABLE videos ADD COLUMN source TEXT DEFAULT 'upload';
ALTER TABLE videos ADD COLUMN session_id TEXT;
ALTER TABLE videos ADD COLUMN analysis_status TEXT DEFAULT 'pending';
ALTER TABLE videos ADD COLUMN analysis_result_json TEXT;
ALTER TABLE videos ADD COLUMN reference_video_id INTEGER;
```

Recommended `source` values:

- `live`
- `upload`
- `youtube`
- `reference`

Recommended `analysis_status` values:

- `pending`
- `processing`
- `completed`
- `failed`

Recommended indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_videos_exercise_type ON videos(exercise_type);
CREATE INDEX IF NOT EXISTS idx_videos_source ON videos(source);
CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date);
CREATE INDEX IF NOT EXISTS idx_videos_session_id ON videos(session_id);
```

---

## Live video row example

For a live squat recording:

```json
{
  "id": 42,
  "filename": "session_ws_record_127.0.0.1_squat_1718312345.mp4",
  "original_filename": "exercise_session_squat_1718312345.mp4",
  "upload_date": "2026-06-14T23:22:41",
  "exercise_type": "squat",
  "file_size": 1843200,
  "duration": 15.0,
  "width": 1280,
  "height": 720,
  "description": "Recorded session for squat",
  "source": "live",
  "session_id": "ws_record_127.0.0.1",
  "analysis_status": "completed"
}
```

---

## Video retrieval flow

After SQLite3 insert, backend returns:

```json
{
  "type": "session_complete",
  "video_id": 42,
  "video_url": "/api/videos/42",
  "exercise_type": "squat",
  "duration": 15.0,
  "frames_processed": 150,
  "analysis": {
    "overall_form_score": 78.5,
    "summary": {
      "status": "Needs improvement"
    }
  },
  "feedback": "Keep your knees aligned over your toes..."
}
```

Frontend displays:

- Download button from `sessionComplete.video_url`.
- Exercise type.
- Duration.
- Optional feedback.

---

## Offline analysis flow after live capture

Once the live video is saved and stored in SQLite3:

1. Load video metadata from `videos`.
2. Resolve local file path from:
   - `videos.filename`
   - `backend/data/videos/recordings/`
3. Decode frames with OpenCV.
4. Extract YOLOv8 pose keypoints.
5. Smooth keypoints.
6. Detect reps or key movement moments.
7. Compare against reference video.
8. Store analysis result metadata back to SQLite3.

This makes the live recording reusable for:

- immediate feedback
- later form comparison
- exercise history
- reference delta reports

---

## Reference comparison flow

### Inputs

- Reference video:
  - uploaded file
  - YouTube URL
  - existing saved `videos.id`
- Live/user video:
  - saved live recording from `/ws/record-session`
  - uploaded user video
  - existing `videos.id`

### Processing

1. Decode both videos with OpenCV.
2. Extract pose keypoints from both.
3. Normalize timeline:
   - by rep boundaries, or
   - by normalized timeline, or
   - by DTW.
4. Compute delta features:
   - joint angles
   - depth
   - symmetry
   - range of motion
   - timing
5. Generate summary:
   - mean absolute delta
   - max delta
   - worst frames
   - per-rep score
   - recommendations

### Example delta metrics

```json
{
  "delta_knee_angle_mean": 8.4,
  "delta_hip_angle_mean": 12.1,
  "delta_depth_mean": 0.18,
  "delta_symmetry_mean": 0.09,
  "worst_frame_idx": 47
}
```

---

## Concrete data model

### Live session metadata

Store per live session:

- `session_id`
- `exercise_type`
- `started_at`
- `ended_at`
- `duration_seconds`
- `frames_captured`
- `actual_fps`
- `width`
- `height`
- `video_id`
- `video_path`
- `analysis_status`

### Pose keypoints

Store per analyzed frame:

- frame index
- timestamp
- keypoints: `[(x, y, conf), ...]`
- bbox
- total confidence

### Derived features per frame

Example exercise-agnostic features:

- left/right knee angles
- hip hinge angle
- shoulder-hip alignment angle
- depth proxy
- left/right symmetry score
- rep phase

### Delta metrics

Example schema:

- `delta_knee_angle_mean`
- `delta_hip_angle_mean`
- `delta_depth_mean`
- `delta_symmetry_mean`
- `worst_frame_idx`
- `worst_rep_index`
- `overall_score`

---

## Handling “light video” skeleton failures

Live capture should preserve the original recording even when live skeleton detection is weak.

Add these offline-analysis knobs:

1. **Upscale frames** before inference, for example width `640` or `720`.
2. **Decrease pose confidence threshold** when extracting keypoints.
3. **Increase temporal density** around motion peaks.
4. **Temporal smoothing** so short detection dropouts do not eliminate reps.
5. **Motion-based frame selection**:
   - compute frame-to-frame grayscale difference
   - run full pose detection on frames that exceed the motion threshold
6. **Fallback sampling**:
   - fixed FPS sampling
   - top-k motion frames
   - evenly spaced frames across the full recording

Implementation approach:

- Compute `motion_score[t]`.
- Keep top-k frames per second or frames above a threshold.
- Guarantee at least one frame from the beginning, middle, and end of each detected rep.

---

## API and WebSocket endpoints

### Live recording WebSocket

```text
WS /ws/record-session
```

Client messages:

```json
{
  "config": {
    "exercise_type": "squat",
    "duration_seconds": 15
  }
}
```

```json
{
  "image": "data:image/jpeg;base64,..."
}
```

```json
{
  "command": "stop"
}
```

Server messages:

- `config_ack`
- `recording_started`
- `recording_stopped`
- `session_complete`
- `error`

---

### Video file endpoint

```text
GET /api/videos/{video_id}
```

Returns the saved MP4 file using the SQLite3 `videos` row.

---

### Uploaded video analysis endpoint

```text
POST /api/exercise/track/video
```

Body:

- video file
- exercise type
- optional reference URL

Returns:

- user analysis result
- optional reference comparison
- optional AI guidance

---

### Reference comparison endpoint

```text
POST /api/exercise/compare
```

Body:

```json
{
  "reference_video": "path-or-video-id",
  "user_video": "path-or-video-id",
  "exercise_type": "squat"
}
```

Returns:

- delta metrics
- score
- worst frames
- per-rep summary
- optional overlay artifacts

---

## Repo integration plan

### Existing files to use

- `frontend/src/components/RecordSession.jsx`
  - Live camera UI and capture canvas.

- `frontend/src/hooks/useRecordSession.js`
  - WebSocket recording state and frame transport.

- `backend/src/api/routes.py`
  - WebSocket live recording endpoint.
  - `_process_recorded_video(...)`.
  - `/api/videos/{video_id}` file serving.

- `backend/src/database.py`
  - SQLite3 connection and video metadata helpers.

- `backend/src/services/exercise_form_tracker.py`
  - Reference/user video comparison.

- `backend/src/services/video_analysis_service.py`
  - Single-user video analysis.

---

### Required integration behavior

Live recording should complete this full chain:

```text
Camera frame
  -> canvas JPEG data URL
  -> WebSocket frame message
  -> backend base64 decode
  -> frame list
  -> MP4 file on disk
  -> SQLite3 videos row
  -> /api/videos/{video_id}
  -> pose analysis
  -> optional reference comparison
```

---

### Database behavior

For every completed live recording:

1. `init_db()` must have run before insert.
2. `add_video(...)` must insert a row in SQLite3.
3. The returned `video_id` must be included in `session_complete`.
4. `GET /api/videos/{video_id}` must load the row from SQLite3.
5. If the file is missing, endpoint should return `404`.
6. `delete_video(video_id)` should remove the metadata row and, ideally, delete the file from disk.

---

## Suggested CLI / scripts

### Compare two saved videos

```bash
python -m backend.scripts.compare_form --ref ref.mp4 --user backend/data/videos/recordings/session_ws_record_127.0.0.1_squat_1718312345.mp4 --exercise squat
```

### Analyze latest live session by SQLite3 ID

```bash
python -m backend.scripts.analyze_video --video-id 42 --exercise squat
```

### Compare latest live session against reference video ID

```bash
python -m backend.scripts.compare_form --ref-id 1 --user-id 42 --exercise squat
```

---

## What to deliver (minimum viable)

1. A live recording flow that:
   - captures camera frames
   - saves an MP4 file
   - stores video metadata in SQLite3
   - returns a playable video URL

2. A saved-video analysis flow that:
   - loads the live recording from disk using SQLite3 metadata
   - extracts pose keypoints
   - computes exercise form metrics

3. A reference comparison flow that:
   - compares the saved live video against a reference video
   - computes delta features
   - returns a summary report

4. Optional:
   - skeleton overlay images
   - worst-frame artifacts
   - rep-by-rep comparison table
   - SQLite3 analysis result JSON

---

## Next step to implement immediately

Fastest path:

1. Keep the existing live capture WebSocket path.
2. Ensure every completed live session writes:
   - MP4 file to `backend/data/videos/recordings/`
   - metadata row to SQLite3 `videos`
   - `video_id` back to the frontend
3. Use that saved live MP4 as the `user_video` input for `backend/src/services/exercise_form_tracker.py`.
4. Compare it against a reference video.
5. Store the comparison result back in SQLite3 as `analysis_result_json` when schema evolution is allowed.

---

## Acceptance criteria

The live capture and SQLite3 persistence feature is complete when:

- Starting a live session opens the camera.
- Recording captures frames until stop or duration expiry.
- Backend saves a playable MP4 file.
- SQLite3 contains a new `videos` row for the captured session.
- Frontend receives `video_id` and `video_url`.
- `GET /api/videos/{video_id}` returns the saved live video.
- The saved live video can be analyzed by the exercise form tracker.
- The saved live video can be compared against a reference video.
- Deletion removes the SQLite3 row and the corresponding file.

---

## Notes about frontend/live skeleton vs offline tracker

- Live recording UI can work even when detection quality is lower.
- Live skeleton overlay is optional and should not block saving the video.
- Offline comparison requires correctness:
  - strict confidence handling
  - smoothing
  - motion-aware sampling
  - alignment
  - delta computation
- It is normal to see skeleton “not appear” on some light videos in real time, while offline analysis still works when confidence and sampling are tuned.
