import os
import cv2
import numpy as np
from backend.services.advanced_emotion import EmotionEngine

def test_pipeline():
    # 1. Initialize services
    print("Testing EmotionEngine...")
    engine = EmotionEngine()
    assert engine.model is not None
    assert engine.detector is not None

    # 2. Test with blank image (should return no faces)
    print("Testing with blank image...")
    blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
    faces = engine.process_frame_as_dicts(blank_img)
    assert len(faces) == 0, f"Detector found a face in a blank image: {faces}"
    
    # 3. Test prediction mapping structure if a face is present
    print("Testing predictor mapping on a structured mock image...")
    mock_img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.circle(mock_img, (320, 240), 90, (255, 255, 255), -1)
    
    predictions = engine.process_frame_as_dicts(mock_img)
    # Check shape of returned results if any mock detection triggers
    for pred in predictions:
        assert pred["face_detected"] is True
        assert pred["emotion"] in ["Neutral", "Happy", "Sad", "Angry", "Fear", "Surprise", "Disgust"]
        assert 0.0 <= pred["confidence"] <= 100.0
        assert len(pred["probabilities"]) == 7
        assert abs(sum(pred["probabilities"].values()) - 100.0) < 1e-4
        
    print("All Advanced Emotion Engine unit tests passed!")

if __name__ == "__main__":
    test_pipeline()
