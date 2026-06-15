"""Create synthetic training data and train classifier.

This demonstrates the training pipeline with sample data.
Generates random good/bad form keypoint data and trains the classifier.
"""
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier


def generate_sample_data(n_good=10, n_bad=10, num_keypoints=17):
    """Generate synthetic good/bad form keypoint data."""
    X = []
    y = []
    
    # Good form: consistent, stable keypoints (lower variance)
    for _ in range(n_good):
        features = []
        for kp_id in range(num_keypoints):
            mean_x = np.random.uniform(100, 400)
            mean_y = np.random.uniform(100, 400)
            std_x = np.random.uniform(5, 15)   # Low variance = stable form
            std_y = np.random.uniform(5, 15)
            features.extend([mean_x, mean_y, std_x, std_y])
        X.append(np.array(features))
        y.append(0)  # 0 = good
    
    # Bad form: inconsistent, erratic keypoints (higher variance)
    for _ in range(n_bad):
        features = []
        for kp_id in range(num_keypoints):
            mean_x = np.random.uniform(80, 420)
            mean_y = np.random.uniform(80, 420)
            std_x = np.random.uniform(25, 50)  # High variance = unstable/poor form
            std_y = np.random.uniform(25, 50)
            features.extend([mean_x, mean_y, std_x, std_y])
        X.append(np.array(features))
        y.append(1)  # 1 = bad
    
    return np.array(X), np.array(y)


def main():
    print("=" * 60)
    print("EXERCISE FORM CLASSIFIER - DEMO TRAINER")
    print("=" * 60)
    
    repo_root = Path(__file__).resolve().parent.parent
    model_dir = repo_root / 'backend' / 'src' / 'models'
    model_path = model_dir / 'form_classifier_model.pkl'
    
    # Generate synthetic training data
    print("\n[1] Generating synthetic training data...")
    print("    - 10 good form samples (stable keypoints, low variance)")
    print("    - 10 bad form samples (unstable keypoints, high variance)")
    X, y = generate_sample_data(n_good=10, n_bad=10)
    print(f"    ✓ Generated {len(X)} samples with {X.shape[1]} features per sample")
    
    # Train-test split
    print("\n[2] Splitting data (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"    ✓ Train: {len(X_train)} samples, Test: {len(X_test)} samples")
    
    # Train XGBoost
    print("\n[3] Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    model.fit(X_train, y_train)
    print("    ✓ Training complete")
    
    # Evaluate
    print("\n[4] Evaluating on test set...")
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n    Test Accuracy: {acc:.1%}")
    print("\n    Classification Report:")
    print("    " + "\n    ".join(classification_report(
        y_test, y_pred, target_names=['Good Form', 'Bad Form']
    ).split('\n')))
    
    # Save model
    print("\n[5] Saving model...")
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, str(model_path))
    print(f"    ✓ Model saved to: {model_path}")
    print(f"    ✓ File size: {model_path.stat().st_size / 1024:.1f} KB")
    
    print("\n" + "=" * 60)
    print("✓ TRAINING COMPLETE - Model ready for use!")
    print("=" * 60)
    print("\nThe trained model is now loaded by the backend API.")
    print("To train on real videos, use: python scripts/download_and_train.py --manifest videos.txt")
    print("\n")


if __name__ == '__main__':
    main()
