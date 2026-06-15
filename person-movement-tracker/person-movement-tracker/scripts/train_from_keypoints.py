"""Train form classifier from existing keypoint CSV files.

Looks for CSV files under `backend/data/keypoints/good_form` and `backend/data/keypoints/bad_form`.
Each CSV is expected to contain rows with columns: frame,keypoint_id,x,y,confidence

Outputs a trained XGBoost model to `backend/src/models/form_classifier_model.pkl` by default.
"""
import os
import sys
from pathlib import Path
import argparse
import glob
import joblib
import numpy as np
import pandas as pd

def extract_features_from_csv(csv_path: str, num_keypoints: int = 17) -> np.ndarray:
    df = pd.read_csv(csv_path)
    if df.empty:
        return np.array([])

    features = []
    for kp_id in range(num_keypoints):
        kp_data = df[df['keypoint_id'] == kp_id]
        if len(kp_data) > 0:
            features.extend([
                float(kp_data['x'].mean()),
                float(kp_data['y'].mean()),
                float(kp_data['x'].std()) if len(kp_data) > 1 else 0.0,
                float(kp_data['y'].std()) if len(kp_data) > 1 else 0.0,
            ])
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])

    return np.array(features)


def gather_features(base_keypoints_dir: Path):
    good_dir = base_keypoints_dir / 'good_form'
    bad_dir = base_keypoints_dir / 'bad_form'

    good_files = list(good_dir.glob('*.csv'))
    bad_files = list(bad_dir.glob('*.csv'))

    X = []
    y = []

    for f in good_files:
        feat = extract_features_from_csv(str(f))
        if feat.size > 0:
            X.append(feat)
            y.append(0)

    for f in bad_files:
        feat = extract_features_from_csv(str(f))
        if feat.size > 0:
            X.append(feat)
            y.append(1)

    return np.array(X), np.array(y)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keypoints-dir', default=os.path.join('backend','data','keypoints'), help='Base keypoints directory')
    parser.add_argument('--output', default=os.path.join('backend','src','models','form_classifier_model.pkl'), help='Output model path')
    parser.add_argument('--test-size', type=float, default=0.2)
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    repo_root = base_dir.parent

    keypoints_dir = Path(args.keypoints_dir)
    if not keypoints_dir.is_absolute():
        keypoints_dir = repo_root / args.keypoints_dir

    if not keypoints_dir.exists():
        print(f'Keypoints directory not found: {keypoints_dir}')
        sys.exit(2)

    print(f'Gathering keypoint CSVs from: {keypoints_dir}')
    X, y = gather_features(keypoints_dir)

    print(f'Found samples: {len(X)} (good={int((y==0).sum())}, bad={int((y==1).sum())})')

    if len(X) < 2:
        print('Not enough samples to train. Need at least one sample per class.')
        sys.exit(3)

    try:
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report, accuracy_score
        from xgboost import XGBClassifier
    except Exception as e:
        print('Missing dependencies for training:', e)
        print('Install: pip install xgboost scikit-learn joblib pandas')
        sys.exit(4)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=args.test_size, random_state=42, stratify=y)

    print('Training XGBoost classifier...')
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
    acc = accuracy_score(y_test, y_pred)
    print(f'Test Accuracy: {acc:.3f}')
    print('\nClassification Report:\n')
    print(classification_report(y_test, y_pred, target_names=['Good','Bad']))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, str(out_path))
    print(f'Model saved to: {out_path}')


if __name__ == '__main__':
    main()
