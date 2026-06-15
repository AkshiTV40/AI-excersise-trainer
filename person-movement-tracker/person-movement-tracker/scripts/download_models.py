#!/usr/bin/env python3
"""
Download AI models for Person Movement Tracker
"""
import os
import sys

def download_models():
    print("Downloading AI models for Person Movement Tracker...")
    print("=" * 60)
    
    # Create models directory
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    try:
        # Download YOLOv8
        print("\n1. Downloading YOLOv8...")
        from ultralytics import YOLO
        yolo_model = YOLO('yolov8n.pt')
        print("   YOLOv8 downloaded successfully!")
        
    except Exception as e:
        print(f"   Error downloading YOLOv8: {e}")
    
    try:
        # Download HuggingFace models
        print("\n2. Downloading HuggingFace models...")
        from transformers import AutoModelForObjectDetection, AutoImageProcessor
        
        models = [
            'facebook/detr-resnet-50',
            'hustvl/yolos-small',
        ]
        
        for model_id in models:
            print(f"   Downloading {model_id}...")
            try:
                processor = AutoImageProcessor.from_pretrained(
                    model_id, 
                    cache_dir=models_dir
                )
                model = AutoModelForObjectDetection.from_pretrained(
                    model_id, 
                    cache_dir=models_dir
                )
                print(f"   {model_id} downloaded successfully!")
            except Exception as e:
                print(f"   Error downloading {model_id}: {e}")
    
    except ImportError:
        print("   transformers not installed. Skipping HuggingFace models.")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Model download complete!")
    print(f"Models saved to: {models_dir}")

if __name__ == "__main__":
    download_models()