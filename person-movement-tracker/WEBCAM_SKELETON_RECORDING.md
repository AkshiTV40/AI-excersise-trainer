# Save Webcam Stream + Skeleton Overlay (One Video Location)

This adds a **reliable offline capture script** that:
- Captures webcam stream
- Draws **MediaPipe Pose skeleton** on every frame
- Saves the result to **one specified output path** (default: `pose_skeleton_output.mp4` in the repo root)

## 1) Install dependencies

```bash
pip install opencv-python mediapipe
```

## 2) Usage

Record and save with skeleton overlay:

```bash
python save_webcam_stream.py --output saved_video.mp4 --fps 20 --width 640 --height 480
```

Stop recording by pressing **`q`** in the preview window.

### Options
- `--camera`: camera index (default `0`)
- `--output`: output filename/path
- `--fps`: output FPS
- `--width`, `--height`: output resolution

## 3) “Video saves in 1 place only” guarantee

The script uses the `--output` argument to open a single `cv2.VideoWriter` and writes every processed frame to that one file.

If you want the file always in one directory, set `--output` accordingly, e.g.:

```bash
python save_webcam_stream.py --output ./recordings/pose_skeleton_output.mp4
```

## 4) Notes about light videos (skeleton missing)

When skeleton is missing on some videos, common causes are:
- too low frame resolution
- pose confidence thresholds too high
- sparse frame sampling

For the realtime webcam script, the pose estimator is configured with:
- `min_detection_conf` and `min_tracking_conf` defaults to `0.5`

You can lower them if needed:

```bash
python save_webcam_stream.py --min_det_conf 0.3 --min_track_conf 0.3
```

