import cv2
import numpy as np
from typing import Dict, Tuple, Any

def get_laplacian_variance(face_img: np.ndarray) -> float:
    """
    Computes the Laplacian variance to measure image sharpness/blurriness.
    """
    if face_img is None or face_img.size == 0:
        return 0.0
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def estimate_head_pose_degrees(landmarks: Dict[str, Tuple[int, int]]) -> Tuple[float, float]:
    """
    Estimates approximate head Yaw and Pitch angles in degrees from 2D landmarks.
    Works by comparing relative horizontal and vertical distances of landmarks.
    """
    try:
        # Landmarks: right_eye, left_eye, nose_tip, mouth_center, right_ear, left_ear
        re_x, re_y = landmarks["right_eye"]
        le_x, le_y = landmarks["left_eye"]
        nt_x, nt_y = landmarks["nose_tip"]
        mc_x, mc_y = landmarks["mouth_center"]
        
        # 1. Yaw (Left-Right rotation) estimation:
        # Calculate horizontal distance ratio: (nose_to_left_eye) vs (nose_to_right_eye)
        # Note: right_eye is left-most on screen, left_eye is right-most on screen.
        dx_left = nt_x - re_x
        dx_right = le_x - nt_x
        
        if dx_left <= 0 or dx_right <= 0:
            # High profiles
            yaw = 45.0
        else:
            ratio = dx_left / dx_right
            # Straight ahead ratio is close to 1.0. We map ratio to degrees.
            # Angle ~ arctan( (ratio-1)/(ratio+1) ) * scaling
            yaw = abs(np.degrees(np.arctan((ratio - 1.0) / (ratio + 1.0))) * 1.5)

        # 2. Pitch (Up-Down tilt) estimation:
        # Find midpoint of eye-line
        eye_mid_y = (re_y + le_y) / 2
        # Vertical height from eyes to mouth
        face_height = max(1.0, mc_y - eye_mid_y)
        # Vertical height from eyes to nose tip
        nose_offset = nt_y - eye_mid_y
        
        # Standard ratio (nose vertical offset / face height) is around 0.4 - 0.45.
        pitch_ratio = nose_offset / face_height
        pitch = abs((pitch_ratio - 0.43) * 90.0)
        
        return float(yaw), float(pitch)
        
    except Exception:
        # Safe fallback
        return 0.0, 0.0

def evaluate_face_quality(
    face_img: np.ndarray, 
    landmarks: Dict[str, Tuple[int, int]],
    min_resolution: int = 40,
    blur_threshold: float = 60.0,
    yaw_limit: float = 35.0,
    pitch_limit: float = 30.0
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates the quality of a cropped face.
    Returns: (is_valid, rejection_reason, metrics_dict)
    """
    metrics = {
        "width": 0,
        "height": 0,
        "blur_score": 0.0,
        "yaw": 0.0,
        "pitch": 0.0
    }

    if face_img is None or face_img.size == 0:
        return False, "Empty frame", metrics

    h, w = face_img.shape[:2]
    metrics["width"] = w
    metrics["height"] = h

    # 1. Size Check
    if w < min_resolution or h < min_resolution:
        return False, f"Resolution too low ({w}x{h} px)", metrics

    # 2. Blur check
    blur_score = get_laplacian_variance(face_img)
    metrics["blur_score"] = float(blur_score)
    if blur_score < blur_threshold:
        return False, f"Face blurry (score: {blur_score:.1f} < {blur_threshold})", metrics

    # 3. Head pose check
    yaw, pitch = estimate_head_pose_degrees(landmarks)
    metrics["yaw"] = yaw
    metrics["pitch"] = pitch
    
    if yaw > yaw_limit:
        return False, f"Head yaw too extreme ({yaw:.1f} deg > {yaw_limit})", metrics
    if pitch > pitch_limit:
        return False, f"Head pitch too extreme ({pitch:.1f} deg > {pitch_limit})", metrics

    return True, "Passed Quality Check", metrics
