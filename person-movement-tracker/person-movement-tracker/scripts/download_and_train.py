"""Download and organize labeled videos (YouTube, local, etc.) for training.

Three workflows:

1. Download from manifest (direct to training folders):
   python scripts/download_and_train.py --manifest urls.txt
   Format: label,url  (e.g., good,https://youtube.com/watch?v=...)

2. Download to custom folder (organize first, then train):
   python scripts/download_and_train.py --manifest urls.txt --output-dir C:\\downloads\\videos
   (Then manually organize into good_form/ and bad_form/ subfolders, then use workflow 3)

3. Organize existing folder and train:
   python scripts/download_and_train.py --organize-from C:\\downloads\\videos
   (Expects custom folder to have good_form/ and bad_form/ subfolders)

Manifest format (one line per video, no header):
  good,https://www.youtube.com/watch?v=...
  bad,https://www.youtube.com/watch?v=...
  good_form,https://example.com/video.mp4
  # comments start with #

Requires: pip install yt-dlp
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def normalize_label(l: str) -> str:
    l = l.strip().lower()
    if l in ('good', 'good_form'):
        return 'good_form'
    if l in ('bad', 'bad_form'):
        return 'bad_form'
    return l.replace(' ', '_')


def download_video(url: str, out_dir: Path) -> bool:
    """Download video using yt-dlp. Returns True on success."""
    import sys
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '--merge-output-format', 'mp4',
        '-o', str(out_dir / '%(title).200s.%(ext)s'),
        url
    ]
    print(f'  Downloading: {url}')
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f'  ✓ Downloaded to {out_dir}')
            return True
        else:
            print(f'  ✗ Download failed')
            if result.stderr:
                print(f'    Error: {result.stderr[:200]}')
            return False
    except Exception as e:
        print(f'  ✗ Error: {e}')
        return False


def organize_videos(src_dir: Path, repo_root: Path) -> int:
    """Copy videos from src_dir/good_form and bad_form to training folders."""
    src_dir = src_dir.resolve()
    good_src = src_dir / 'good_form'
    bad_src = src_dir / 'bad_form'
    
    if not good_src.exists() and not bad_src.exists():
        print(f'  ✗ Source folder does not contain good_form/ or bad_form/: {src_dir}')
        return 0
    
    videos_base = repo_root / 'backend' / 'data' / 'videos'
    good_dest = videos_base / 'good_form'
    bad_dest = videos_base / 'bad_form'
    
    count = 0
    for src_folder, dest_folder, label in [(good_src, good_dest, 'good_form'), (bad_src, bad_dest, 'bad_form')]:
        if not src_folder.exists():
            print(f'  ⊘ {label}/ not found in {src_dir}')
            continue
        
        dest_folder.mkdir(parents=True, exist_ok=True)
        files = list(src_folder.glob('*'))
        video_files = [f for f in files if f.is_file()]
        
        if not video_files:
            print(f'  ⊘ No videos in {src_folder.name}/')
            continue
        
        print(f'  Copying {len(video_files)} {label} video(s)...')
        for video_file in video_files:
            dest_file = dest_folder / video_file.name
            try:
                shutil.copy2(video_file, dest_file)
                count += 1
                print(f'    ✓ {video_file.name}')
            except Exception as e:
                print(f'    ✗ Failed to copy {video_file.name}: {e}')
    
    return count


def run_training(repo_root: Path) -> bool:
    """Run training on prepared videos. Returns True on success."""
    trainer = repo_root / 'train_form_classifier.py'
    if not trainer.exists():
        print(f'  ✗ Training script not found: {trainer}')
        return False
    
    print('\n[*] Starting training...')
    cmd = ['python', str(trainer)]
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f'  ✗ Training failed with error: {e}')
        return False
    except Exception as e:
        print(f'  ✗ Error: {e}')
        return False


def main():
    parser = argparse.ArgumentParser(description='Download and train on exercise videos.')
    parser.add_argument('--manifest', help='CSV file: label,url')
    parser.add_argument('--output-dir', help='Save downloads to custom folder (instead of training folder)')
    parser.add_argument('--organize-from', help='Copy videos from custom folder to training folders')
    parser.add_argument('--repo-root', default='.', help='Repository root')
    parser.add_argument('--skip-train', action='store_true', help='Download/organize only, skip training')
    args = parser.parse_args()
    
    repo_root = Path(args.repo_root).resolve()
    print(f'Using repository root: {repo_root}\n')
    
    downloaded = False
    organized = False
    
    if args.manifest:
        # Workflow 1 & 2: Download from manifest
        manifest_path = Path(args.manifest)
        if not manifest_path.is_absolute():
            manifest_path = Path.cwd() / manifest_path
        
        if not manifest_path.exists():
            print(f'✗ Manifest file not found: {manifest_path}')
            return
        
        if args.output_dir:
            # Workflow 2: Download to custom folder
            output_base = Path(args.output_dir).resolve()
            print(f'[Workflow 2] Downloading to custom folder: {output_base}\n')
        else:
            # Workflow 1: Download directly to training folder
            output_base = repo_root / 'backend' / 'data' / 'videos'
            print(f'[Workflow 1] Downloading to training folder: {output_base}\n')
        
        print(f'Reading manifest: {manifest_path}')
        count = 0
        with open(manifest_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    label, url = line.split(',', 1)
                    url = url.strip()
                except ValueError:
                    print(f'  ⊘ Skipping invalid line: {line}')
                    continue
                
                label = normalize_label(label)
                out_dir = output_base / label
                if download_video(url, out_dir):
                    count += 1
        
        if count > 0:
            print(f'✓ Downloaded {count} video(s) to: {output_base}')
            downloaded = True
        else:
            print(f'⊘ No videos were successfully downloaded')
        
        if args.output_dir:
            print(f'\nNext step: Organize videos into:')
            print(f'  {args.output_dir}/good_form/')
            print(f'  {args.output_dir}/bad_form/')
            print(f'\nThen run:')
            print(f'  python scripts/download_and_train.py --organize-from "{args.output_dir}" --repo-root "{repo_root}"')
    
    if args.organize_from:
        # Workflow 3: Organize and copy to training folder
        print(f'\n[Workflow 3] Organizing videos from: {args.organize_from}\n')
        count = organize_videos(Path(args.organize_from), repo_root)
        if count > 0:
            print(f'\n✓ Organized {count} video(s) into training folders')
            organized = True
        else:
            print(f'\n✗ No videos were organized. Check folder structure.')
    
    # Train if:
    # - We downloaded directly to training (Workflow 1) without --output-dir AND not --skip-train
    # - OR we organized from external folder (Workflow 3) AND not --skip-train
    should_train = not args.skip_train and (
        (downloaded and not args.output_dir) or organized
    )
    
    if should_train:
        run_training(repo_root)


if __name__ == '__main__':
    main()
