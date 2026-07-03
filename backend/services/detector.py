import os
import cv2
import logging
from typing import List, Tuple, Any
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

logger = logging.getLogger("backend.services.detector")

class FaceDetector:
    def __init__(self) -> None:
        logger.info("Initializing MediaPipe Tasks Face Detector...")
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(current_dir, "models", "blaze_face_short_range.tflite")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"MediaPipe face detector model file not found at {model_path}")
            
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(base_options=base_options, min_detection_confidence=0.45)
        self.detector = vision.FaceDetector.create_from_options(options)
        logger.info("MediaPipe Tasks Face Detector initialized successfully.")

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[Tuple[int, int, int, int], np.ndarray]]:
        """
        Detects faces in a BGR frame and returns a list of:
        ((x, y, w, h), aligned_face_crop)
        Where (x, y, w, h) is the original bounding box, and aligned_face_crop is the aligned BGR crop.
        """
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        
        # Convert BGR to RGB (MediaPipe requirement)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image object
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Run detection
        detection_result = self.detector.detect(mp_image)
        
        faces = []
        if not detection_result.detections:
            return faces
            
        for detection in detection_result.detections:
            # 1. Extract bounding box in absolute pixels
            bbox = detection.bounding_box
            x = int(bbox.origin_x)
            y = int(bbox.origin_y)
            width = int(bbox.width)
            height = int(bbox.height)
            
            # Clamp coordinates to frame boundary
            x = max(0, x)
            y = max(0, y)
            width = min(width, w - x)
            height = min(height, h - y)
            
            if width <= 0 or height <= 0:
                continue
                
            # 2. Extract eye landmarks (indices: 0 = right eye, 1 = left eye)
            if len(detection.keypoints) >= 2:
                right_eye = detection.keypoints[0]
                left_eye = detection.keypoints[1]
                
                re_x, re_y = int(right_eye.x * w), int(right_eye.y * h)
                le_x, le_y = int(left_eye.x * w), int(left_eye.y * h)
                
                # Compute roll angle and eye center
                d_y = le_y - re_y
                d_x = le_x - re_x
                angle = np.degrees(np.arctan2(d_y, d_x))
                eye_center = ((re_x + le_x) // 2, (re_y + le_y) // 2)
            else:
                # Fallback if keypoints are missing
                angle = 0.0
                eye_center = (x + width // 2, y + height // 2)
                
            # 3. Rotate the frame around the eye center to align
            rot_matrix = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
            rotated_frame = cv2.warpAffine(frame, rot_matrix, (w, h), flags=cv2.INTER_CUBIC)
            
            # 4. Crop a square centered around the eye center
            # Pad size slightly to keep facial landmarks well inside the crop
            face_size = int(max(width, height) * 1.1)
            crop_cx = eye_center[0]
            crop_cy = int(eye_center[1] + face_size * 0.15)
            
            crop_x1 = int(crop_cx - face_size * 0.6)
            crop_y1 = int(crop_cy - face_size * 0.6)
            crop_x2 = int(crop_cx + face_size * 0.6)
            crop_y2 = int(crop_cy + face_size * 0.6)
            
            crop_x1_clamped = max(0, crop_x1)
            crop_y1_clamped = max(0, crop_y1)
            crop_x2_clamped = min(w, crop_x2)
            crop_y2_clamped = min(h, crop_y2)
            
            cropped_face = rotated_frame[crop_y1_clamped:crop_y2_clamped, crop_x1_clamped:crop_x2_clamped]
            
            # Draw back border padding for out-of-bounds crops
            target_w = crop_x2 - crop_x1
            target_h = crop_y2 - crop_y1
            if cropped_face.size > 0 and (cropped_face.shape[1] != target_w or cropped_face.shape[0] != target_h):
                pad_top = crop_y1_clamped - crop_y1
                pad_bottom = crop_y2 - crop_y2_clamped
                pad_left = crop_x1_clamped - crop_x1
                pad_right = crop_x2 - crop_x2_clamped
                cropped_face = cv2.copyMakeBorder(
                    cropped_face, pad_top, pad_bottom, pad_left, pad_right,
                    cv2.BORDER_CONSTANT, value=[0, 0, 0]
                )
                
            faces.append(((x, y, width, height), cropped_face))
            
        return faces
