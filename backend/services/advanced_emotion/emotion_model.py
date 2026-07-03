import logging
import numpy as np
import onnxruntime as ort

logger = logging.getLogger("backend.services.advanced_emotion.emotion_model")

class AdvancedEmotionModel:
    def __init__(self, model_path: str) -> None:
        logger.info(f"Loading HSEmotion ONNX Model from: {model_path}")
        
        # Load ONNX Session using CPU Execution Provider (standard for server hosting)
        self.ort_session = ort.InferenceSession(
            model_path, 
            providers=['CPUExecutionProvider']
        )
        
        # Discover dynamically input/output tensor names
        self.input_name = self.ort_session.get_inputs()[0].name
        self.output_name = self.ort_session.get_outputs()[0].name
        
        logger.info(f"ONNX Model loaded. Input: '{self.input_name}', Output: '{self.output_name}'")

    def predict_raw_probabilities(self, preprocessed_tensor: np.ndarray) -> np.ndarray:
        """
        Runs model inference on a preprocessed face tensor [1, 3, 224, 224]
        and returns a normalized 8-class probability distribution array (summing to 1.0).
        """
        if preprocessed_tensor is None:
            return np.zeros(8, dtype=np.float32)

        # Run inference session
        outputs = self.ort_session.run(
            [self.output_name], 
            {self.input_name: preprocessed_tensor}
        )
        
        # Extract raw logit scores
        logits = outputs[0][0]  # Shape: (8,)
        
        # Apply numerical-stable Softmax activation to convert logits to probabilities
        e_x = np.exp(logits - np.max(logits))
        probabilities = e_x / e_x.sum()
        
        return probabilities
