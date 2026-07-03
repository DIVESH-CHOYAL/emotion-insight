import os
import cv2
import logging
from typing import List, Tuple
import numpy as np

from backend import config

logger = logging.getLogger("backend.services.detector")

class FaceDetector:
    def __init__(self) -> None:
        cascade_path = config.CASCADE_PATH
        logger.info(f"Loading Haar Cascade face detector from {cascade_path}...")
        
        if not os.path.exists(cascade_path):
            raise FileNotFoundError(f"Haar Cascade XML not found at {cascade_path}")
            
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar Cascade face classifier.")
        logger.info("FaceDetector Haar Cascade loaded successfully.")

    def detect_faces(self, gray_frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detects faces in a grayscale frame and returns bounding boxes (x, y, w, h).
        """
        faces = self.face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.3,
            minNeighbors=5
        )
        return [tuple(face) for face in faces]
