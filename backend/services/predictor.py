import cv2
import logging
from typing import Tuple, Dict
import numpy as np

# Workaround for hsemotion-onnx internal import bug
import urllib.request
from hsemotion_onnx.facial_emotions import HSEmotionRecognizer

logger = logging.getLogger("backend.services.predictor")

class EmotionPredictor:
    def __init__(self) -> None:
        logger.info("Initializing EmotionPredictor with HSEmotion enet_b2_7...")
        # enet_b2_7 is a high-accuracy, lightweight model trained on AffectNet (7 classes)
        self.fer = HSEmotionRecognizer(model_name='enet_b2_7')
        logger.info("EmotionPredictor initialized successfully.")

    def predict_emotion(self, face_img: np.ndarray) -> Tuple[str, float]:
        """
        Runs prediction on a face crop BGR image and returns (dominant_emotion, confidence_percentage).
        """
        probs = self.predict_probabilities(face_img)
        if not probs:
            return "Neutral", 0.0
            
        dominant_emotion = max(probs, key=probs.get)
        confidence = probs[dominant_emotion]
        return dominant_emotion, confidence

    def predict_probabilities(self, face_img: np.ndarray) -> Dict[str, float]:
        """
        Runs prediction and returns a dictionary of probabilities mapped to [0, 100] percentage.
        """
        if face_img is None or face_img.size == 0:
            return {}

        try:
            # Predict using crop BGR image directly (HSEmotion handles resizing and normalization internally)
            # logits=False applies softmax to get normalized probabilities
            _, probs7 = self.fer.predict_emotions(face_img, logits=False)
            
            # Map HSEmotion class indices to our standard frontend labels:
            # {0: 'Anger', 1: 'Disgust', 2: 'Fear', 3: 'Happiness', 4: 'Neutral', 5: 'Sadness', 6: 'Surprise'}
            raw_probs = {
                "Angry": float(probs7[0]) * 100.0,
                "Disgust": float(probs7[1]) * 100.0,
                "Fear": float(probs7[2]) * 100.0,
                "Happy": float(probs7[3]) * 100.0,
                "Neutral": float(probs7[4]) * 100.0,
                "Sad": float(probs7[5]) * 100.0,
                "Surprise": float(probs7[6]) * 100.0
            }
            
            # Print detailed debug logs for evaluation (Task 4)
            logger.info(f"--- Predictor Debug ---")
            logger.info(f"Input image shape: {face_img.shape}")
            logger.info(f"HSEmotion raw scores (8-class softmax): {[round(float(v) * 100, 2) for v in probs7]}")
            logger.info(f"Mapped 7-class probabilities: {raw_probs}")
            logger.info(f"-----------------------")
            
            return raw_probs
            
        except Exception as e:
            logger.error(f"Error predicting facial emotion: {e}")
            # Fallback to safe defaults in case of error
            return {
                "Neutral": 100.0,
                "Happy": 0.0,
                "Surprise": 0.0,
                "Sad": 0.0,
                "Angry": 0.0,
                "Disgust": 0.0,
                "Fear": 0.0
            }
