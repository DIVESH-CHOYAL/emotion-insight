import cv2
import numpy as np
from typing import Dict, Tuple

def align_and_crop_face(
    frame: np.ndarray, 
    landmarks: Dict[str, Tuple[int, int]], 
    bbox: Tuple[int, int, int, int],
    target_size: int = 224
) -> np.ndarray:
    """
    Aligns the face upright by rotating the frame based on the eyes angle,
    then crops a square bounding box.
    """
    if frame is None or frame.size == 0:
        return None

    h, w = frame.shape[:2]
    x, y, width, height = bbox

    # 1. Extract eye landmarks for roll angle calculation
    right_eye = landmarks.get("right_eye")
    left_eye = landmarks.get("left_eye")

    if right_eye and left_eye:
        re_x, re_y = right_eye
        le_x, le_y = left_eye
        
        # Calculate angle of rotation in degrees
        dy = le_y - re_y
        dx = le_x - re_x
        angle = np.degrees(np.arctan2(dy, dx))
        eye_center = ((re_x + le_x) // 2, (re_y + le_y) // 2)
    else:
        angle = 0.0
        eye_center = (x + width // 2, y + height // 2)

    # 2. Perform rotation transformation
    rot_matrix = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
    rotated_frame = cv2.warpAffine(frame, rot_matrix, (w, h), flags=cv2.INTER_CUBIC)

    # 3. Crop a square centered slightly below the eye center (around facial center)
    face_scale = int(max(width, height) * 1.1)
    crop_cx = eye_center[0]
    crop_cy = int(eye_center[1] + face_scale * 0.15)  # Offset down slightly from eyes

    crop_x1 = int(crop_cx - face_scale * 0.6)
    crop_y1 = int(crop_cy - face_scale * 0.6)
    crop_x2 = int(crop_cx + face_scale * 0.6)
    crop_y2 = int(crop_cy + face_scale * 0.6)

    # Clamp coordinates to frame boundary for safe cropping
    crop_x1_clamped = max(0, crop_x1)
    crop_y1_clamped = max(0, crop_y1)
    crop_x2_clamped = min(w, crop_x2)
    crop_y2_clamped = min(h, crop_y2)

    cropped_face = rotated_frame[crop_y1_clamped:crop_y2_clamped, crop_x1_clamped:crop_x2_clamped]

    # 4. Pad boundaries with black border if crop goes out-of-bounds
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

    # Resize to target size for the model
    if cropped_face.size > 0:
        return cv2.resize(cropped_face, (target_size, target_size))
    return None
