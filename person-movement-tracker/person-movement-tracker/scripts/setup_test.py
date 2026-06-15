from pathlib import Path

# Create test structure
test_dir = Path('C:/tmp/test_videos')
test_dir.mkdir(parents=True, exist_ok=True)
(test_dir / 'good_form').mkdir(exist_ok=True)
(test_dir / 'bad_form').mkdir(exist_ok=True)

# Create dummy video files
(test_dir / 'good_form' / 'squat_good.mp4').touch()
(test_dir / 'good_form' / 'pushup_good.mp4').touch()
(test_dir / 'bad_form' / 'squat_bad.mp4').touch()

print(f'✓ Created test structure at: {test_dir}')
print(f'  - good_form: {list((test_dir / "good_form").glob("*"))}')
print(f'  - bad_form: {list((test_dir / "bad_form").glob("*"))}')
