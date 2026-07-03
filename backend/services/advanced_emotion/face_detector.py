import os
import cv2
import logging
from typing import List, Dict, Any
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

logger = logging.getLogger("backend.services.advanced_emotion.face_detector")

class AdvancedFaceDetector:
    def __init__(self, model_path: str, min_confidence: float = 0.45) -> None:
        logger.info(f"Initializing MediaPipe Face Detector from path: {model_path}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"MediaPipe face detector model file not found at {model_path}")
            
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options, 
            min_detection_confidence=min_confidence
        )
        self.detector = vision.FaceDetector.create_from_options(options)
        logger.info("MediaPipe Face Detector successfully loaded.")

    def detect_faces_raw(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs MediaPipe face detection and returns a list of dictionaries with raw coordinates:
        [
            {
                "bbox": [x, y, w, h],
                "landmarks": {
                    "right_eye": (x, y),
                    "left_eye": (x, y),
                    "nose_tip": (x, y),
                    "mouth_center": (x, y),
                    "right_ear": (x, y),
                    "left_ear": (x, y)
                },
                "score": float
            },
            ...
        ]
        """
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        
        # MediaPipe requires RGB format
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        detection_result = self.detector.detect(mp_image)
        
        raw_faces = []
        if not detection_result.detections:
            return raw_faces

        for detection in detection_result.detections:
            # Bounding box extraction
            bbox = detection.bounding_box
            rx, ry = int(bbox.origin_x), int(bbox.origin_y)
            rw, rh = int(bbox.width), int(bbox.height)

            # Clamp coordinates to frame boundary
            x = max(0, rx)
            y = max(0, ry)
            width = min(rw, w - x)
            height = min(rh, h - y)

            if width <= 0 or height <= 0:
                continue

            # Keypoints extraction (indices: 0=right eye, 1=left eye, 2=nose, 3=mouth, 4=right ear, 5=left ear)
            landmarks = {}
            keypoint_names = ["right_eye", "left_eye", "nose_tip", "mouth_center", "right_ear", "left_ear"]
            
            for idx, kp_name in enumerate(keypoint_names):
                if len(detection.keypoints) > idx:
                    kp = detection.keypoints[idx]
                    landmarks[kp_name] = (int(kp.x * w), int(kp.y * h))
                else:
                    # Fallback fallback
                    landmarks[kp_name] = (x + width // 2, y + height // 2)

            score = float(detection.categories[0].score) if detection.categories else 0.0

            raw_faces.append({
                "bbox": [x, y, width, height],
                "landmarks": landmarks,
                "score": score
            })

        return raw_faces
