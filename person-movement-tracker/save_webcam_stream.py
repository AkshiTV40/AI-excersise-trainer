import argparse
import os
from pathlib import Path

import cv2

try:
    import mediapipe as mp
except ImportError as e:
    raise SystemExit(
        "MediaPipe is required for skeleton overlay. Install with: pip install mediapipe"
    ) from e


def parse_args():
    p = argparse.ArgumentParser(description="Save webcam stream with pose skeleton overlay (MediaPipe).")
    p.add_argument("--output", default="pose_skeleton_output.mp4", help="Output video filename")
    p.add_argument("--camera", type=int, default=0, help="Camera index")
    p.add_argument("--fps", type=float, default=20.0, help="Output FPS")
    p.add_argument("--width", type=int, default=640, help="Frame width")
    p.add_argument("--height", type=int, default=480, help="Frame height")
    p.add_argument("--min_det_conf", type=float, default=0.5, help="Min detection confidence")
    p.add_argument("--min_track_conf", type=float, default=0.5, help="Min tracking confidence")
    p.add_argument("--model_complexity", type=int, default=1, help="MediaPipe pose model complexity (0/1/2)")
    return p.parse_args()


def main():
    args = parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Error: Could not open the webcam (camera index {args.camera}).")

    # Force resolution (helps ensure encoder + writer match exactly)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or args.width
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or args.height

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, float(args.fps), (frame_width, frame_height))
    if not writer.isOpened():
        raise RuntimeError(f"Error: Could not open VideoWriter for output file: {out_path}")

    # MediaPipe Pose
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    pose_estimator = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=int(args.model_complexity),
        enable_segmentation=False,
        min_detection_confidence=float(args.min_det_conf),
        min_tracking_confidence=float(args.min_track_conf),
    )

    print(f"Recording started. Saving to: {out_path}")
    print("Press 'q' to stop and save.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("Warning: Failed to fetch live camera frame. Stopping.")
                break

            # Ensure frame size is exactly the writer size
            frame = cv2.resize(frame, (frame_width, frame_height), interpolation=cv2.INTER_LINEAR)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose_estimator.process(rgb)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style(),
                )

            writer.write(frame)
            cv2.imshow("Live Local Pose Tracking... (MediaPipe)", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        writer.release()
        cv2.destroyAllWindows()
        pose_estimator.close()

    print(f"Video file saved successfully to: {out_path.resolve()}")


if __name__ == "__main__":
    main()

