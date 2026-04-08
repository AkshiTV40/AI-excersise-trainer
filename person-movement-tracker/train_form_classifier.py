"""
Exercise Form Model Training Script
Extracts keypoints from videos and trains an XGBoost classifier

Usage:
1. Place good form videos in: data/videos/good_form/
2. Place bad form videos in: data/videos/bad_form/
3. Run: python train_form_classifier.py
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import cv2
import joblib
from glob import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    from xgboost import XGBClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
except ImportError as e:
    logger.error(f"Missing dependencies: {e}")
    logger.info("Install: pip install ultralytics xgboost scikit-learn")
    sys.exit(1)


class KeypointExtractor:
    """Extract keypoints from videos using YOLO"""
    
    KEYPOINT_NAMES = [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ]
    
    def __init__(self, model_name: str = "yolov8n-pose.pt"):
        logger.info(f"Loading YOLO model: {model_name}")
        self.model = YOLO(model_name)
    
    def extract_from_video(self, video_path: str, frame_skip: int = 1) -> list:
        """Extract keypoints from all frames in a video"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"Cannot open video: {video_path}")
            return []
        
        all_keypoints = []
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % frame_skip == 0:
                results = self.model(frame, verbose=False)
                if results and results[0].keypoints is not None:
                    keypoints_data = results[0].keypoints
                    if len(keypoints_data.xy) > 0:
                        coords = keypoints_data.xy[0]
                        confs = keypoints_data.conf[0]
                        
                        frame_kps = []
                        for i, (x, y) in enumerate(coords):
                            if i < len(self.KEYPOINT_NAMES):
                                c = confs[i].item() if i < len(confs) else 0.0
                                frame_kps.append({
                                    'keypoint_id': i,
                                    'x': float(x.item()),
                                    'y': float(y.item()),
                                    'confidence': float(c)
                                })
                        
                        if frame_kps:
                            all_keypoints.append({
                                'frame': frame_idx,
                                'keypoints': frame_kps
                            })
            
            frame_idx += 1
        
        cap.release()
        return all_keypoints
    
    def save_keypoints_to_csv(self, keypoints_data: list, output_path: str):
        """Save keypoints to CSV format"""
        rows = []
        for frame_data in keypoints_data:
            frame = frame_data['frame']
            for kp in frame_data['keypoints']:
                rows.append({
                    'frame': frame,
                    'keypoint_id': kp['keypoint_id'],
                    'x': kp['x'],
                    'y': kp['y'],
                    'confidence': kp['confidence']
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(rows)} keypoints to {output_path}")


class FeatureExtractor:
    """Extract features from keypoint CSV data"""
    
    KEYPOINT_NAMES = [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ]
    
    def extract_from_csv(self, csv_path: str) -> np.ndarray:
        """Extract features from keypoints CSV"""
        df = pd.read_csv(csv_path)
        
        if df.empty:
            return np.array([])
        
        features = []
        
        for kp_id in range(len(self.KEYPOINT_NAMES)):
            kp_data = df[df['keypoint_id'] == kp_id]
            
            if len(kp_data) > 0:
                features.extend([
                    kp_data['x'].mean(),
                    kp_data['y'].mean(),
                    kp_data['x'].std() if len(kp_data) > 1 else 0,
                    kp_data['y'].std() if len(kp_data) > 1 else 0
                ])
            else:
                features.extend([0, 0, 0, 0])
        
        return np.array(features)


def process_videos(video_dir: str, output_dir: str, label: int, extractor: KeypointExtractor):
    """Process all videos in a directory"""
    os.makedirs(output_dir, exist_ok=True)
    
    video_patterns = ["*.mp4", "*.MP4", "*.avi", "*.mov"]
    video_files = []
    for pattern in video_patterns:
        video_files.extend(glob(os.path.join(video_dir, pattern)))
    
    logger.info(f"Found {len(video_files)} videos in {video_dir}")
    
    all_features = []
    
    for video_path in video_files:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        logger.info(f"Processing: {video_name}")
        
        keypoints = extractor.extract_from_video(video_path, frame_skip=3)
        
        if keypoints:
            csv_path = os.path.join(output_dir, f"{video_name}_keypoints.csv")
            extractor.save_keypoints_to_csv(keypoints, csv_path)
            
            temp_csv = csv_path
            feat_extractor = FeatureExtractor()
            features = feat_extractor.extract_from_csv(temp_csv)
            
            if len(features) > 0:
                all_features.append(features)
    
    return all_features


def main():
    parser = argparse.ArgumentParser(description="Train exercise form classifier")
    parser.add_argument("--good-videos", default="data/videos/good_form", help="Path to good form videos")
    parser.add_argument("--bad-videos", default="data/videos/bad_form", help="Path to bad form videos")
    parser.add_argument("--output", default="models/form_classifier_model.pkl", help="Output model path")
    parser.add_argument("--yolo-model", default="yolov8n-pose.pt", help="YOLO model name")
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent / "backend"
    data_dir = base_dir / "data"
    
    good_videos_path = args.good_videos if os.path.isabs(args.good_videos) else data_dir / args.good_videos
    bad_videos_path = args.bad_videos if os.path.isabs(args.bad_videos) else data_dir / args.bad_videos
    
    logger.info("=== Starting Exercise Form Model Training ===")
    
    extractor = KeypointExtractor(model_name=args.yolo_model)
    
    good_output = data_dir / "keypoints" / "good_form"
    bad_output = data_dir / "keypoints" / "bad_form"
    
    logger.info("Processing good form videos...")
    good_features = process_videos(str(good_videos_path), str(good_output), 0, extractor)
    logger.info(f"Extracted features from {len(good_features)} good form videos")
    
    logger.info("Processing bad form videos...")
    bad_features = process_videos(str(bad_videos_path), str(bad_output), 1, extractor)
    logger.info(f"Extracted features from {len(bad_features)} bad form videos")
    
    if len(good_features) == 0 or len(bad_features) == 0:
        logger.error("Insufficient data for training. Need both good and bad form videos.")
        sys.exit(1)
    
    X = np.array(good_features + bad_features)
    y = np.array([0] * len(good_features) + [1] * len(bad_features))
    
    logger.info(f"Total samples: {len(X)}, Features: {X.shape[1]}")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info("Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"Test Accuracy: {accuracy:.2f}")
    logger.info("\nClassification Report:\n" + classification_report(y_test, y_pred, target_names=["Good Form", "Bad Form"]))
    
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    joblib.dump(model, args.output)
    logger.info(f"Model saved to: {args.output}")
    
    logger.info("=== Training Complete ===")


if __name__ == "__main__":
    main()