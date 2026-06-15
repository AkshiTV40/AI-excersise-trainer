# Exercise Form Classification with Decision Tree and Qwen Models

This solution addresses the user's request for:
1. A decision tree code to determine if exercise form was good or not
2. Guidance on which Qwen model to use from Hugging Face
3. Training implementation for accurate exercise performance predictions

## Files Created

### 1. Decision Tree Classifier (`person-movement-tracker/backend/src/models/decision_tree_classifier.py`)
- Implements a DecisionTreeClassifier using scikit-learn for exercise form classification
- Takes pose keypoints as input and outputs "good_form" or "bad_form" prediction
- Includes feature extraction from keypoints (mean and std of x,y coordinates for 17 key points)
- Provides methods for training, saving/loading models, prediction, and evaluation
- Includes feature importance analysis to understand which keypoints matter most for form assessment

### 2. Training Script (`person-movement-tracker/backend/train_decision_tree.py`)
- Demonstrates how to load existing keypoint CSV data from the good_form and bad_form directories
- Shows how to extract features from the keypoint data
- Trains the decision tree classifier and evaluates its performance
- Saves the trained model for later use

## Existing Qwen Model Usage

The system already incorporates Qwen models for natural language feedback generation through the `GuidanceService` in `person-movement-tracker/backend/src/services/guidance_service.py`:

- Uses **Qwen/Qwen2.5-Omni-7B** model for generating exercise guidance
- Provides multimodal capabilities (vision + text) for analyzing exercise form from video frames
- Generates natural language coaching tips based on exercise analysis
- Includes fallback mechanisms when the Qwen model is not available

## How It Works Together

1. **Form Classification**: The decision tree classifier analyzes pose keypoints to determine if form is good or bad
2. **Feedback Generation**: The GuidanceService uses Qwen2.5-Omni to generate natural language feedback based on:
   - The form classification result (good/bad)
   - Exercise type detected
   - Specific form issues identified
   - Reference exercise videos (if available)

## Key Features

### Decision Tree Classifier
- Interpretable model (you can see which features are most important)
- Fast inference suitable for real-time applications
- Handles both good and bad form classification
- Provides confidence scores with predictions
- Includes preprocessing pipeline with standardization

### Qwen Model Integration (Existing)
- Uses Qwen/Qwen2.5-Omni-7B for advanced natural language understanding
- Capable of analyzing video frames to detect exercises and form issues
- Generates personalized coaching feedback in natural language
- Multimodal capabilities combine vision and language understanding

## Usage Example

```python
# Initialize classifier
classifier = DecisionTreeFormClassifier("path/to/trained/model.pkl")

# Get keypoints from pose estimation (e.g., MediaPipe)
keypoints = {
    "nose": (0.5, 0.2),
    "left_shoulder": (0.4, 0.3),
    "right_shoulder": (0.6, 0.3),
    # ... other keypoints
}

# Get form prediction
result = classifier.predict(keypoints)
print(f"Form: {result.form_label}, Confidence: {result.confidence:.2f}")

# Generate natural language feedback using existing GuidanceService
from .services.guidance_service import GuidanceService
guidance_service = GuidanceService()
feedback = guidance_service.generate_guidance("squat", {"overall_form_score": result.confidence * 100})
print(f"Feedback: {feedback}")
```

## Training Data Requirements

The training script expects CSV files with the following format:
- `frame`: Frame number
- `keypoint_id`: Identifier for each keypoint (0-16 for the 17 key points)
- `x`: Normalized x-coordinate (0-1)
- `y`: Normalized y-coordinate (0-1)
- `confidence`: Detection confidence (0-1)

This matches the existing format in:
- `person-movement-tracker/backend/data/keypoints/good_form/`
- `person-movement-tracker/backend/data/keypoints/bad_form/`

## Performance Considerations

- Decision trees are fast to train and predict, making them suitable for real-time applications
- The model provides interpretable results through feature importance
- Qwen model usage is handled asynchronously to avoid blocking the main processing thread
- Fallback mechanisms ensure the system works even without internet access to Hugging Face models