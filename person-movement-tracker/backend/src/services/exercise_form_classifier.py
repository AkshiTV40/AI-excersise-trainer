"""
Exercise Form Classifier Service
Uses XGBoost to classify exercise form as good or bad based on pose keypoints
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

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
    Classifier for exercise form using XGBoost
    Classifies form as good (0) or bad (1) based on pose keypoints
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the classifier
        
        Args:
            model_path: Path to saved model file (optional)
        """
        self.feature_extractor = KeypointFeatureExtractor([
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle"
        ])
        
        self.model = None
        self.model_loaded = False
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        elif not XGBOOST_AVAILABLE:
            logger.warning("XGBoost not available. Classifier will use heuristic mode.")
    
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
            logger.info(f"Model loaded from {model_path}")
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
        if not self.model:
            return False
        
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            joblib.dump(self.model, model_path)
            logger.info(f"Model saved to {model_path}")
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
        if not XGBOOST_AVAILABLE:
            logger.error("XGBoost not available for training")
            return False
        
        try:
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            self.model.fit(X_train, y_train)
            self.model_loaded = True
            self.is_trained = True
            logger.info("Model trained successfully")
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
        if not self.is_trained or not self.model:
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
        if not self.is_trained or not self.model:
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
            df = pd.DataFrame(keypoints_data)
            df.to_csv(output_path, index=False)
            logger.info(f"Keypoints saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save keypoints: {e}")
            return False
    
    @staticmethod
    def load_keypoints_from_csv(csv_path: str) -> pd.DataFrame:
        """
        Load keypoints from CSV file
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            DataFrame with keypoints data
        """
        try:
            return pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to load keypoints: {e}")
            return pd.DataFrame()