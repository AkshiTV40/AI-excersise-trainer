"""
Test script for Decision Tree Form Classifier
"""

import numpy as np
import sys
import os

# Add the src directory to the path so we can import from models
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.decision_tree_classifier import DecisionTreeFormClassifier

def test_decision_tree_classifier():
    """Test the decision tree classifier with dummy data"""
    print("Testing Decision Tree Form Classifier...")
    
    # Create classifier
    classifier = DecisionTreeFormClassifier()
    
    # Create some dummy training data
    # 64 features (17 keypoints * 2 for mean/std)
    X_train = np.random.rand(50, 64)
    y_train = np.random.randint(0, 2, 50)  # Random labels
    
    # Train the classifier
    print("Training classifier...")
    success = classifier.train(X_train, y_train)
    
    if not success:
        print("ERROR: Training failed!")
        return False
    
    print("Training successful!")
    
    # Test prediction
    print("Testing prediction...")
    dummy_keypoints = {name: (0.5, 0.5) for name in [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ]}
    
    result = classifier.predict(dummy_keypoints)
    print(f"Prediction: {result.form_label}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Is good form: {result.is_good_form}")
    
    # Test saving and loading
    print("Testing model save/load...")
    import os
    model_path = "test_model.pkl"
    
    save_success = classifier.save_model(model_path)
    if not save_success:
        print("ERROR: Failed to save model!")
        return False
    
    print("Model saved successfully!")
    
    # Load the model
    new_classifier = DecisionTreeFormClassifier(model_path)
    if not new_classifier.is_trained:
        print("ERROR: Failed to load model!")
        return False
    
    print("Model loaded successfully!")
    
    # Test prediction with loaded model
    result2 = new_classifier.predict(dummy_keypoints)
    print(f"Loaded model prediction: {result2.form_label}")
    print(f"Loaded model confidence: {result2.confidence:.2f}")
    
    # Clean up
    if os.path.exists(model_path):
        os.remove(model_path)
    
    print("All tests passed!")
    return True

if __name__ == "__main__":
    test_decision_tree_classifier()