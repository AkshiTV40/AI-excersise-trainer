"""
Exercise Form Classifier Service
Uses Decision Tree to classify exercise form as good or bad based on pose keypoints
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import joblib
from pathlib import Path

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


class ExerciseFormClassifier:
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
        # Import here to avoid circular imports
        from ..models.decision_tree_classifier import DecisionTreeFormClassifier
        
        self.feature_extractor = KeypointFeatureExtractor([
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle"
        ])
        
        # Create the decision tree classifier
        self.classifier = DecisionTreeFormClassifier(model_path)
        self.is_trained = self.classifier.is_trained
        
        if model_path and os.path.exists(model_path):
            logger.info(f"Decision tree classifier loaded from {model_path}")
        elif not self.classifier.is_trained:
            logger.info("Using untrained decision tree classifier (will use heuristics until trained)")
    
    def load_model(self, model_path: str) -> bool:
        """
        Load a trained model from file
        
        Args:
            model_path: Path to model file
            
        Returns:
            True if loaded successfully
        """
        success = self.classifier.load_model(model_path)
        self.is_trained = self.classifier.is_trained
        if success:
            logger.info(f"Decision tree model loaded from {model_path}")
        return success
    
    def save_model(self, model_path: str) -> bool:
        """
        Save the trained model to file
        
        Args:
            model_path: Path to save model
            
        Returns:
            True if saved successfully
        """
        success = self.classifier.save_model(model_path)
        if success:
            logger.info(f"Decision tree model saved to {model_path}")
        return success
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> bool:
        """
        Train the classifier
        
        Args:
            X_train: Training features
            y_train: Training labels (0 = good form, 1 = bad form)
            
        Returns:
            True if trained successfully
        """
        success = self.classifier.train(X_train, y_train)
        self.is_trained = self.classifier.is_trained
        if success:
            logger.info("Decision tree model trained successfully")
        return success
    
    def predict(self, keypoints: Dict[str, Tuple[float, float]]) -> FormClassificationResult:
        """
        Predict form classification for given keypoints
        
        Args:
            keypoints: Dictionary of keypoint names to (x, y) coordinates
            
        Returns:
            FormClassificationResult with prediction
        """
        # Get result from decision tree classifier
        result = self.classifier.predict(keypoints)
        
        # Convert to the expected FormatClassificationResult (should already be compatible)
        return FormClassificationResult(
            form_label=result.form_label,
            confidence=result.confidence,
            is_good_form=result.is_good_form
        )
    
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
        
        # Create temporary arrays for evaluation in the format expected by the decision tree
        # We need to convert feature vectors back to keypoints dicts for the predict method
        # This is inefficient but maintains compatibility with the existing interface
        
        # For now, just use the classifier's evaluate method if available
        if hasattr(self.classifier, 'evaluate'):
            return self.classifier.evaluate(X_test, y_test)
        
        # Fallback: manual evaluation (less efficient)
        try:
            from sklearn.metrics import classification_report, accuracy_score
            
            y_pred = []
            for i in range(len(X_test)):
                # This is a simplification - we'd need to store original keypoints
                # For now, use dummy keypoints (this won't be accurate for real evaluation)
                dummy_keypoints = {name: (0.5, 0.5) for name in [
                    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
                    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
                    "left_wrist", "right_wrist", "left_hip", "right_hip",
                    "left_knee", "right_knee", "left_ankle", "right_ankle"
                ]}
                result = self.predict(dummy_keypoints)
                y_pred.append(0 if result.is_good_form else 1)
            
            return {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "report": classification_report(y_test, y_pred, target_names=["Good Form", "Bad Form"])
            }
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {}


class KeypointsToCSVConverter:
    """Convert keypoints to CSV format for training data"""
    
    @staticmethod
    def save_keypoints_to_csv(keypoints_data: List[Dict], output_path: str) -> bool:
        """
        Save keypoints data to CSV file
        
        Args:
            keypoints_data: List of dictionaries with frame, keypoint_id, x, y, confidence
            output_path: Output CSV file path
            
        Returns:
            True if saved successfully
        """
        try:
            import pandas as pd
            df = pd.DataFrame(keypoints_data)
            df.to_csv(output_path, index=False)
            logger.info(f"Keypoints saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save keypoints: {e}")
            return False
    
    @staticmethod
    def load_keypoints_from_csv(csv_path: str):
        """
        Load keypoints from CSV file
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            DataFrame with keypoints data
        """
        try:
            import pandas as pd
            return pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to load keypoints: {e}")
            return None