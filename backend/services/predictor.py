import numpy as np
import cv2
import logging
from typing import Tuple, Dict
from backend.services.model_loader import ModelLoader

logger = logging.getLogger("backend.services.predictor")

class EmotionPredictor:
    EMOTION_DICT: Dict[int, str] = {
        0: "Angry", 
        1: "Disgusted", 
        2: "Fearful", 
        3: "Happy", 
        4: "Neutral", 
        5: "Sad", 
        6: "Surprised"
    }

    def __init__(self) -> None:
        self.model = ModelLoader.get_model()
        logger.info("EmotionPredictor initialized successfully.")

    def predict_emotion(self, roi_gray: np.ndarray) -> Tuple[str, float]:
        """
        Resizes the grayscale face ROI to 48x48, normalizes it, runs prediction,
        and returns the (emotion_label, confidence_percentage).
        """
        resized = cv2.resize(roi_gray, (48, 48))
        normalized = resized.astype("float32") / 255.0
        input_data = np.expand_dims(np.expand_dims(normalized, -1), 0)
        
        predictions = self.model(input_data, training=False).numpy()
        max_idx = int(np.argmax(predictions[0]))
        emotion = self.EMOTION_DICT[max_idx]
        confidence = float(predictions[0][max_idx]) * 100.0
        
        return emotion, confidence

    def predict_probabilities(self, roi_gray: np.ndarray) -> Dict[str, float]:
        """
        Returns a dictionary of all emotion classes mapped to their confidence percentage.
        """
        resized = cv2.resize(roi_gray, (48, 48))
        normalized = resized.astype("float32") / 255.0
        input_data = np.expand_dims(np.expand_dims(normalized, -1), 0)
        
        predictions = self.model(input_data, training=False).numpy()[0]
        return {self.EMOTION_DICT[i]: float(score) * 100.0 for i, score in enumerate(predictions)}
