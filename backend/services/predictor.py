import cv2
import logging
from typing import Tuple, Dict
import numpy as np
from backend.services.model_loader import ModelLoader

logger = logging.getLogger("backend.services.predictor")

def softmax(x: np.ndarray) -> np.ndarray:
    """Computes softmax values for a set of logits."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

class EmotionPredictor:
    def __init__(self) -> None:
        logger.info("Initializing EmotionPredictor ONNX Session...")
        self.session = ModelLoader.get_model()
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        logger.info("EmotionPredictor ONNX session initialized successfully.")

    def _preprocess(self, face_img: np.ndarray) -> np.ndarray:
        """
        Preprocesses a BGR face crop into a [1, 1, 64, 64] float32 normalized grayscale tensor.
        """
        # Convert to grayscale if it is in color
        if len(face_img.shape) == 3 and face_img.shape[2] == 3:
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_img

        # Resize to 64x64 as required by the FER+ model
        resized = cv2.resize(gray, (64, 64))
        
        # Convert to float32 (values in [0, 255] range as required by FER+ ONNX model)
        preprocessed = resized.astype("float32")
        
        # Expand dimensions to fit [1, 1, 64, 64] shape
        input_data = np.expand_dims(np.expand_dims(preprocessed, axis=0), axis=0)
        return input_data

    def predict_emotion(self, face_img: np.ndarray) -> Tuple[str, float]:
        """
        Runs prediction on a face crop and returns (dominant_emotion, confidence_percentage).
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

        # Preprocess the crop
        input_data = self._preprocess(face_img)
        
        # Run inference
        outputs = self.session.run([self.output_name], {self.input_name: input_data})
        logits = outputs[0][0]
        
        # Apply softmax to convert logits to probabilities
        probs8 = softmax(logits)
        
        # Map 8 FER+ classes to the 7 required classes (Happiness -> Happy, etc. Contempt index 7 is ignored)
        raw_probs = {
            "Neutral": float(probs8[0]),
            "Happy": float(probs8[1]),
            "Surprise": float(probs8[2]),
            "Sad": float(probs8[3]),
            "Angry": float(probs8[4]),
            "Disgust": float(probs8[5]),
            "Fear": float(probs8[6])
        }
        
        # Log debug information
        logger.info(f"--- Predictor Debug ---")
        logger.info(f"Input shape: {input_data.shape}, dtype: {input_data.dtype}")
        logger.info(f"Input pixels - min: {input_data.min():.1f}, max: {input_data.max():.1f}, mean: {input_data.mean():.1f}")
        logger.info(f"Raw logits: {[round(float(v), 4) for v in logits]}")
        logger.info(f"Softmax probabilities (8-class): {[round(float(v) * 100, 2) for v in probs8]}")
        logger.info(f"Mapped 7-class probabilities: {raw_probs}")
        logger.info(f"-----------------------")
        
        # Re-normalize remaining 7 classes to sum to exactly 1.0 (100%)
        total_prob = sum(raw_probs.values())
        if total_prob > 0:
            for k in raw_probs:
                raw_probs[k] = (raw_probs[k] / total_prob) * 100.0
        else:
            raw_probs = {k: 100.0 / 7.0 for k in raw_probs}
            
        return raw_probs
