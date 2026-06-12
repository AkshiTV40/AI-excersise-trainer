"""Prepare data and run training using existing labeled videos.

Usage:
  python scripts/prepare_and_train.py --source-root <path-to-labeled-videos>

The source root should contain two subfolders: `good_form` and `bad_form`, each
with video files. The script copies videos into `backend/data/videos/` and
runs `train_form_classifier.py` from the repo root.
"""
import argparse
import shutil
import subprocess
from pathlib import Path
import sys
import glob


VIDEO_PATTERNS = ["*.mp4", "*.MP4", "*.avi", "*.mov"]


def copy_videos(src_dir: Path, dst_dir: Path) -> int:
    dst_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for pat in VIDEO_PATTERNS:
        for p in src_dir.glob(pat):
            try:
                shutil.copy2(p, dst_dir / p.name)
                count += 1
            except Exception as e:
                print(f"Failed to copy {p}: {e}")
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, help="Path containing good_form/ and bad_form/ subfolders")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], help="Path to repo root")
    parser.add_argument("--yolo-model", default="yolov8n-pose.pt")
    args = parser.parse_args()

    source_root = Path(args.source_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if not source_root.exists():
        print(f"Source root does not exist: {source_root}")
        sys.exit(2)

    good_src = source_root / "good_form"
    bad_src = source_root / "bad_form"

    if not good_src.exists() or not bad_src.exists():
        print("Source root must contain 'good_form' and 'bad_form' subfolders with videos.")
        sys.exit(3)

    dst_base = repo_root / "backend" / "data" / "videos"
    good_dst = dst_base / "good_form"
    bad_dst = dst_base / "bad_form"

    print(f"Copying good videos from {good_src} -> {good_dst}")
    gcount = copy_videos(good_src, good_dst)
    print(f"Copied {gcount} good videos")

    print(f"Copying bad videos from {bad_src} -> {bad_dst}")
    bcount = copy_videos(bad_src, bad_dst)
    print(f"Copied {bcount} bad videos")

    if gcount == 0 or bcount == 0:
        print("Insufficient videos copied; need at least one video in each class.")
        sys.exit(4)

    # Run training
    print("Running training script...")
    try:
        proc = subprocess.run([sys.executable, str(repo_root / "train_form_classifier.py"), "--yolo-model", args.yolo_model, "--output", str(repo_root / "backend" / "src" / "models" / "form_classifier_model.pkl")], cwd=str(repo_root), check=False)
        print(f"Training finished with exit code {proc.returncode}")
        sys.exit(proc.returncode)
    except Exception as e:
        print(f"Failed to run training: {e}")
        sys.exit(10)


if __name__ == "__main__":
    main()
