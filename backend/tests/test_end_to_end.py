import os
import cv2
import numpy as np
from backend.services.detector import FaceDetector
from backend.services.predictor import EmotionPredictor
from backend.services.model_loader import ModelLoader

def test_pipeline():
    # 1. Initialize services
    print("Testing ModelLoader...")
    session = ModelLoader.get_model()
    assert session is not None, "ModelLoader failed to load ONNX session"
    
    print("Testing EmotionPredictor...")
    predictor = EmotionPredictor()
    assert predictor.session is not None
    
    print("Testing FaceDetector...")
    detector = FaceDetector()
    assert detector.detector is not None

    # 2. Test with blank image (should return no faces)
    print("Testing with blank image...")
    blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
    faces = detector.detect_faces(blank_img)
    assert len(faces) == 0, "Detector found a face in a blank image"
    
    # 3. Test prediction mapping with mock input image crop
    print("Testing predictor mapping...")
    mock_crop = np.zeros((100, 100, 3), dtype=np.uint8)
    emotion, confidence = predictor.predict_emotion(mock_crop)
    assert emotion in ["Neutral", "Happy", "Sad", "Angry", "Fear", "Surprise", "Disgust"]
    assert 0.0 <= confidence <= 100.0
    
    probs = predictor.predict_probabilities(mock_crop)
    assert len(probs) == 7
    assert abs(sum(probs.values()) - 100.0) < 1e-4
    
    print("All pipeline integration tests passed!")

if __name__ == "__main__":
    test_pipeline()
