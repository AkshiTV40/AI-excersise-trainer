# Video Download & Training Guide

This guide shows how to download exercise videos and use them to train your form classifier.

## Installation

First, install `yt-dlp` (required for downloading):

```bash
pip install yt-dlp
```

## Three Workflows

### Workflow 1: Quick Download + Train
Download videos directly to training folder and train immediately.

1. Create a manifest file (e.g., `my_videos.txt`):
```
good,https://www.youtube.com/watch?v=VIDEO_ID_1
bad,https://www.youtube.com/watch?v=VIDEO_ID_2
```

2. Run:
```bash
python scripts/download_and_train.py --manifest my_videos.txt
```

This downloads videos into `backend/data/videos/good_form/` and `backend/data/videos/bad_form/` and automatically starts training.

---

### Workflow 2: Download to Custom Folder (Organize Later)
Download to a separate folder first, organize manually, then train.

Useful if you want to:
- Download videos once and organize/review them
- Add videos incrementally  
- Separate download and training into different sessions

1. Create manifest:
```
good,https://www.youtube.com/watch?v=VIDEO_ID_1
bad,https://www.youtube.com/watch?v=VIDEO_ID_2
```

2. Download to custom folder:
```bash
python scripts/download_and_train.py --manifest my_videos.txt --output-dir C:\MyVideoFolder
```

3. Videos are saved to:
   - `C:\MyVideoFolder\good_form\`
   - `C:\MyVideoFolder\bad_form\`

4. Later, organize them if needed, then copy to training:
```bash
python scripts/download_and_train.py --organize-from C:\MyVideoFolder
```

This copies all videos to `backend/data/videos/` and trains.

---

### Workflow 3: Use Existing Videos
If you already have videos in a folder:

1. Organize them into this structure:
```
MyVideos/
  good_form/
    video1.mp4
    video2.mp4
  bad_form/
    video3.mp4
    video4.mp4
```

2. Copy to training and train:
```bash
python scripts/download_and_train.py --organize-from C:\MyVideos
```

---

## Manifest Format

Create a text file with one line per video:

```
label,url
```

- **label**: `good`, `bad`, `good_form`, or `bad_form` (case-insensitive)
- **url**: YouTube, Vimeo, or direct MP4 URL
- Lines starting with `#` are comments

Example:
```
# My exercise videos
good,https://www.youtube.com/watch?v=ABC123
bad,https://www.youtube.com/watch?v=XYZ789
good_form,https://example.com/squat.mp4
# bad,https://www.youtube.com/watch?v=test  (commented out)
```

---

## Tips

1. **YouTube Videos**: Make sure videos are publicly accessible.
2. **Video Length**: Shorter clips (15-60 seconds) train faster.
3. **Quality**: Clear, well-lit videos work better for pose detection.
4. **Skip Training**: Add `--skip-train` to download without training:
   ```bash
   python scripts/download_and_train.py --manifest my_videos.txt --skip-train
   ```
5. **Check Progress**: Training logs show how many videos were found and processed.

---

## Sample Manifest

A `video_manifest_example.txt` is provided with placeholder YouTube video IDs. Update the URLs to real videos and run:

```bash
python scripts/download_and_train.py --manifest scripts/video_manifest_example.txt
```

---

## Output

After training completes, you'll see:
- Test accuracy of the trained model
- Classification report (precision, recall, F1)
- Model saved to `backend/src/models/form_classifier_model.pkl`

The trained model will be used by the backend API automatically.
