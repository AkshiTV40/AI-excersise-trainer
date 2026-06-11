"""
Training script for Decision Tree Form Classifier
Demonstrates how to train the decision tree classifier on exercise keypoint data
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Import our custom classifier
from src.models.decision_tree_classifier import DecisionTreeFormClassifier, create_training_data_from_keypoints


def prepare_data_from_existing_keypoints():
    """
    Prepare training data from the existing keypoint CSV files in the data directory
    """
    good_form_dir = "data/keypoints/good_form"
    bad_form_dir = "data/keypoints/bad_form"
    
    # Define keypoint names in order corresponding to keypoint_id 0-16
    KEYPOINT_NAMES = [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ]
    
    # Initialize feature extractor
    from src.models.decision_tree_classifier import KeypointFeatureExtractor
    feature_extractor = KeypointFeatureExtractor(KEYPOINT_NAMES)
    
    features = []
    labels = []
    
    # Process good form files
    print("Processing good form files...")
    if os.path.exists(good_form_dir):
        for filename in os.listdir(good_form_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(good_form_dir, filename)
                try:
                    df = pd.read_csv(filepath)
                    
                    # Group by frame to get all keypoints for each frame
                    grouped = df.groupby('frame')
                    
                    for frame_num, group in grouped:
                        # Create keypoints dictionary for this frame
                        keypoints_dict = {}
                        for _, row in group.iterrows():
                            keypoint_id = int(row['keypoint_id'])
                            if keypoint_id < len(KEYPOINT_NAMES):
                                keypoints_dict[KEYPOINT_NAMES[keypoint_id]] = (row['x'], row['y'])
                        
                        # Extract features
                        feature_vector = feature_extractor.extract_from_dict(keypoints_dict)
                        if feature_vector:  # Only add if we got valid features
                            features.append(feature_vector)
                            labels.append(0)  # 0 for good form
                            
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    # Process bad form files
    print("Processing bad form files...")
    if os.path.exists(bad_form_dir):
        for filename in os.listdir(bad_form_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(bad_form_dir, filename)
                try:
                    df = pd.read_csv(filepath)
                    
                    # Group by frame to get all keypoints for each frame
                    grouped = df.groupby('frame')
                    
                    for frame_num, group in grouped:
                        # Create keypoints dictionary for this frame
                        keypoints_dict = {}
                        for _, row in group.iterrows():
                            keypoint_id = int(row['keypoint_id'])
                            if keypoint_id < len(KEYPOINT_NAMES):
                                keypoints_dict[KEYPOINT_NAMES[keypoint_id]] = (row['x'], row['y'])
                        
                        # Extract features
                        feature_vector = feature_extractor.extract_from_dict(keypoints_dict)
                        if feature_vector:  # Only add if we got valid features
                            features.append(feature_vector)
                            labels.append(1)  # 1 for bad form
                            
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    print(f"Prepared {len(features)} samples ({sum(1 for l in labels if l == 0)} good, {sum(1 for l in labels if l == 1)} bad)")
    
    if len(features) == 0:
        raise ValueError("No training data could be loaded from the keypoint files")
    
    return np.array(features), np.array(labels)


def train_and_evaluate():
    """
    Train the decision tree classifier and evaluate its performance
    """
    print("Loading training data...")
    X, y = prepare_data_from_existing_keypoints()
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Create and train the classifier
    print("Training Decision Tree classifier...")
    classifier = DecisionTreeFormClassifier()
    
    # Train the model
    success = classifier.train(X_train, y_train)
    
    if not success:
        print("Training failed!")
        return
    
    # Evaluate on test set
    print("Evaluating on test set...")
    eval_result = classifier.evaluate(X_test, y_test)
    if eval_result:
        accuracy = eval_result["accuracy"]
        report = eval_result["report"]
        
        print(f"\nAccuracy: {accuracy:.4f}")
        print("\nClassification Report:")
        print(report)
        
        # Feature importance
        importance = classifier.get_feature_importance()
        if importance is not None:
            print(f"Number of features: {len(importance)}")
            print(f"Feature importance stats - Mean: {np.mean(importance):.4f}, Std: {np.std(importance):.4f}")
    else:
        print("Evaluation failed!")
    
    # Save the model
    model_path = "src/models/decision_tree_form_model.pkl"
    print(f"Saving model to {model_path}...")
    classifier.save_model(model_path)
    
    print("Training completed successfully!")
    return classifier


if __name__ == "__main__":
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        train_and_evaluate()
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()