import os
import logging
from typing import Optional
import onnxruntime as ort

from backend import config

logger = logging.getLogger("backend.services.model_loader")

class ModelLoader:
    _session: Optional[ort.InferenceSession] = None

    @classmethod
    def get_model(cls) -> ort.InferenceSession:
        if cls._session is None:
            cls._session = cls._load_onnx_model()
        return cls._session

    @classmethod
    def _load_onnx_model(cls) -> ort.InferenceSession:
        model_path = config.MODEL_PATH
        logger.info(f"Loading ONNX emotion model from {model_path}...")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ONNX model file not found at {model_path}")
            
        # Initialize the ONNX Runtime InferenceSession
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        logger.info("ONNX emotion model session initialized successfully.")
        return session
