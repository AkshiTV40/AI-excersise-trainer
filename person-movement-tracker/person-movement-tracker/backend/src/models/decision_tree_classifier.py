"""
Decision Tree Classifier for Exercise Form Classification
Uses scikit-learn DecisionTreeClassifier to classify exercise form as good or bad based on pose keypoints
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import joblib
from pathlib import Path

try:
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class FormClassificationResult:
    """Result of form classification"""
    form_label: str  # "good_form" or "bad_form"
    confidence: float
    is_good_form: bool


class KeypointFeatureExtractor:
    """Extracts features from pose keypoints for classification"""
    
    def __init__(self, keypoint_names: List[str]):
        self.keypoint_names = keypoint_names
    
    def extract_features(self, keypoints: List[Tuple[float, float]]) -> List[float]:
        """
        Extract statistical features from keypoints
        
        Args:
            keypoints: List of (x, y) coordinates for each keypoint
            
        Returns:
            List of feature values (mean and std for x, y of each keypoint)
        """
        if not keypoints or len(keypoints) == 0:
            return []
        
        features = []
        
        keypoints_array = np.array(keypoints)
        
        if keypoints_array.ndim == 1:
            keypoints_array = keypoints_array.reshape(-1, 2)
        
        if keypoints_array.shape[1] != 2:
            return []
        
        means = np.mean(keypoints_array, axis=0)
        stds = np.std(keypoints_array, axis=0)
        
        features.extend(means.tolist())
        features.extend(stds.tolist())
        
        return features
    
    def extract_from_dict(self, keypoints_dict: Dict[str, Tuple[float, float]]) -> List[float]:
        """
        Extract features from keypoint dictionary
        
        Args:
            keypoints_dict: Dictionary of keypoint names to (x, y) coordinates
            
        Returns:
            List of feature values
        """
        keypoints = []
        for name in self.keypoint_names:
            if name in keypoints_dict:
                keypoints.append(keypoints_dict[name])
            else:
                keypoints.append((0.0, 0.0))
        
        return self.extract_features(keypoints)


class DecisionTreeFormClassifier:
    """
    Classifier for exercise form using Decision Tree
    Classifies form as good (0) or bad (1) based on pose keypoints
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the classifier
        
        Args:
            model_path: Path to saved model file (optional)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for DecisionTreeFormClassifier")
        
        self.feature_extractor = KeypointFeatureExtractor([
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle"
        ])
        
        # Create a pipeline with preprocessing and classifier
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', DecisionTreeClassifier(
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            ))
        ])
        
        self.model_loaded = False
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> bool:
        """
        Load a trained model from file
        
        Args:
            model_path: Path to model file
            
        Returns:
            True if loaded successfully
        """
        try:
            self.model = joblib.load(model_path)
            self.model_loaded = True
            self.is_trained = True
            logger.info(f"Decision tree model loaded from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def save_model(self, model_path: str) -> bool:
        """
        Save the trained model to file
        
        Args:
            model_path: Path to save model
            
        Returns:
            True if saved successfully
        """
        if not self.is_trained:
            return False
        
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            joblib.dump(self.model, model_path)
            logger.info(f"Decision tree model saved to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> bool:
        """
        Train the classifier
        
        Args:
            X_train: Training features
            y_train: Training labels (0 = good form, 1 = bad form)
            
        Returns:
            True if trained successfully
        """
        try:
            self.model.fit(X_train, y_train)
            self.model_loaded = True
            self.is_trained = True
            logger.info("Decision tree model trained successfully")
            return True
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def predict(self, keypoints: Dict[str, Tuple[float, float]]) -> FormClassificationResult:
        """
        Predict form classification for given keypoints
        
        Args:
            keypoints: Dictionary of keypoint names to (x, y) coordinates
            
        Returns:
            FormClassificationResult with prediction
        """
        if not self.is_trained:
            return self._heuristic_prediction(keypoints)
        
        try:
            features = self.feature_extractor.extract_from_dict(keypoints)
            
            if not features:
                return FormClassificationResult(
                    form_label="unknown",
                    confidence=0.0,
                    is_good_form=False
                )
            
            X = np.array([features])
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            
            confidence = float(max(probabilities))
            is_good_form = bool(prediction == 0)
            
            return FormClassificationResult(
                form_label="good_form" if is_good_form else "bad_form",
                confidence=confidence,
                is_good_form=is_good_form
            )
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return self._heuristic_prediction(keypoints)
    
    def _heuristic_prediction(self, keypoints: Dict[str, Tuple[float, float]]) -> FormClassificationResult:
        """
        Fallback heuristic-based prediction when model is not available
        
        Args:
            keypoints: Dictionary of keypoint names to (x, y) coordinates
            
        Returns:
            FormClassificationResult
        """
        score = 0
        
        if "left_shoulder" in keypoints and "right_shoulder" in keypoints:
            left_shoulder = keypoints["left_shoulder"]
            right_shoulder = keypoints["right_shoulder"]
            
            shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
            if shoulder_diff < 0.05:
                score += 1
        
        if "left_hip" in keypoints and "right_hip" in keypoints:
            left_hip = keypoints["left_hip"]
            right_hip = keypoints["right_hip"]
            
            hip_diff = abs(left_hip[1] - right_hip[1])
            if hip_diff < 0.05:
                score += 1
        
        if "left_knee" in keypoints and "right_knee" in keypoints:
            left_knee = keypoints["left_knee"]
            right_knee = keypoints["right_knee"]
            
            knee_symmetry = abs(left_knee[0] - (1 - right_knee[0]))
            if knee_symmetry < 0.1:
                score += 1
        
        is_good_form = score >= 2
        confidence = min(score / 3.0 + 0.5, 1.0)
        
        return FormClassificationResult(
            form_label="good_form" if is_good_form else "bad_form",
            confidence=confidence,
            is_good_form=is_good_form
        )
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        Evaluate the model on test data
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.is_trained:
            return {}
        
        try:
            from sklearn.metrics import classification_report, accuracy_score
            
            y_pred = self.model.predict(X_test)
            
            return {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "report": classification_report(y_test, y_pred, target_names=["Good Form", "Bad Form"])
            }
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {}
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """
        Get feature importance from the decision tree
        
        Returns:
            Array of feature importance values or None if not trained
        """
        if not self.is_trained:
            return None
        
        try:
            return self.model.named_steps['classifier'].feature_importances_
        except Exception as e:
            logger.error(f"Failed to get feature importance: {e}")
            return None


# Example usage and training function
def create_training_data_from_keypoints(good_form_dir: str, bad_form_dir: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create training data from keypoint CSV files
    
    Args:
        good_form_dir: Directory containing good form keypoint CSV files
        bad_form_dir: Directory containing bad form keypoint CSV files
        
    Returns:
        Tuple of (X, y) where X is features and y is labels (0=good, 1=bad)
    """
    import pandas as pd
    
    feature_extractor = KeypointFeatureExtractor([
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ])
    
    features = []
    labels = []
    
    # Process good form files
    if os.path.exists(good_form_dir):
        for filename in os.listdir(good_form_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(good_form_dir, filename)
                df = pd.read_csv(filepath)
                
                # Extract features for each frame (simplified - in practice you might want to aggregate)
                for _, row in df.iterrows():
                    # Convert row to keypoints dict (this is simplified)
                    keypoints_dict = {}
                    # In a real implementation, you would properly parse the CSV format
                    # For now, we'll skip the detailed implementation
                    pass
    
    # Process bad form files similarly
    # ...
    
    # Return dummy data for now - in practice you would implement the full logic
    X = np.random.rand(100, 64)  # 100 samples, 64 features (32 keypoints * 2 for mean/std)
    y = np.random.randint(0, 2, 100)  # Random labels
    
    return X, y


if __name__ == "__main__":
    # Example usage
    classifier = DecisionTreeFormClassifier()
    
    # Create some dummy training data
    X_train = np.random.rand(100, 64)
    y_train = np.random.randint(0, 2, 100)
    
    # Train the classifier
    classifier.train(X_train, y_train)
    
    # Save the model
    classifier.save_model("person-movement-tracker/backend/src/models/decision_tree_form_model.pkl")
    
    # Make a prediction
    dummy_keypoints = {name: (0.5, 0.5) for name in [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ]}
    
    result = classifier.predict(dummy_keypoints)
    print(f"Prediction: {result.form_label}, Confidence: {result.confidence:.2f}")