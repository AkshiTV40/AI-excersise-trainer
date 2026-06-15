"""Wrapper to run scripts/prepare_and_train.py reliably from any CWD.

Usage:
  python run_prepare_and_train.py --source-root <path-to-labeled-videos>

This resolves the internal script path and calls it with the provided args.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run prepare_and_train helper")
    parser.add_argument("--source-root", required=True, help="Path containing good_form/ and bad_form/ subfolders")
    parser.add_argument("--yolo-model", default="yolov8n-pose.pt", help="YOLO model name to pass through")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    script_path = repo_root / "scripts" / "prepare_and_train.py"

    if not script_path.exists():
        print(f"Could not find helper script at: {script_path}")
        sys.exit(2)

    cmd = [sys.executable, str(script_path), "--source-root", str(args.source_root), "--yolo-model", args.yolo_model]

    proc = subprocess.run(cmd, cwd=str(repo_root))
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
