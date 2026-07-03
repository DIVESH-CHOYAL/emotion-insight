import cv2
import logging
from typing import List, Dict, Tuple, Any, Optional
import numpy as np

from .config import AdvancedEmotionConfig
from .face_detector import AdvancedFaceDetector
from .face_alignment import align_and_crop_face
from .preprocessing import adjust_gamma, apply_clahe, preprocess_for_model
from .tracker import FaceTracker, TrackedFace
from .smoothing import smooth_probabilities_ema
from .postprocessing import evaluate_face_quality, estimate_head_pose_degrees
from .emotion_model import AdvancedEmotionModel
from .emotion_labels import map_probabilities_to_api, API_LABELS

logger = logging.getLogger("backend.services.advanced_emotion.emotion_engine")

class EmotionEngine:
    def __init__(self, config: Optional[AdvancedEmotionConfig] = None) -> None:
        logger.info("Initializing Advanced Emotion Engine...")
        self.config = config or AdvancedEmotionConfig()
        
        # Load Submodules
        self.detector = AdvancedFaceDetector(
            model_path=self.config.FACE_DETECTOR_PATH,
            min_confidence=self.config.MIN_DETECTION_CONFIDENCE
        )
        self.tracker = FaceTracker(
            max_disappeared=self.config.TRACKER_MAX_DISAPPEARED,
            max_distance=self.config.TRACKER_MAX_DISTANCE
        )
        self.model = AdvancedEmotionModel(model_path=self.config.MODEL_PATH)
        
        logger.info("Advanced Emotion Engine loaded successfully.")

    def process_frame(
        self, 
        frame: np.ndarray, 
        draw_overlays: bool = True,
        frame_counter: int = 0,
        frame_skip: int = 3
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Processes a video frame for live detection.
        - Detects faces
        - Tracks faces across frames
        - Performs roll alignment
        - Validates quality (blur, pose)
        - Preprocesses & Runs model inference
        - Smoothes probabilities using EMA
        - Applies a confidence lock cooldown
        - Draws styled overlays
        
        Returns:
            Tuple[annotated_frame, list_of_active_face_predictions]
        """
        if frame is None or frame.size == 0:
            return frame, []

        annotated_frame = frame.copy()
        
        # 1. Raw Face Detection
        raw_detections = self.detector.detect_faces_raw(frame)
        detected_bboxes = [d["bbox"] for d in raw_detections]

        # 2. Update Tracked Faces
        tracked_faces = self.tracker.update(detected_bboxes)
        
        active_predictions = []

        # Map raw detections to tracked faces based on bounding box match
        for face in tracked_faces:
            # Find the corresponding raw detection matching this tracked face's bounding box
            matching_raw = None
            face_x, face_y, face_w, face_h = face.bbox
            face_center = (face_x + face_w // 2, face_y + face_h // 2)

            for raw in raw_detections:
                rx, ry, rw, rh = raw["bbox"]
                # If centroid is very close, it is our raw detection
                dist = np.linalg.norm(np.array(face_center) - np.array((rx + rw // 2, ry + rh // 2)))
                if dist < 40.0:
                    matching_raw = raw
                    break

            if matching_raw is None:
                # No active raw detection for this frame (lost track, predicting with previous state)
                active_predictions.append({
                    "id": face.face_id,
                    "bbox": face.bbox,
                    "emotion": face.current_emotion,
                    "confidence": face.confidence
                })
                continue

            # 3. Align and Crop Face
            aligned_crop = align_and_crop_face(
                frame=frame,
                landmarks=matching_raw["landmarks"],
                bbox=face.bbox,
                target_size=self.config.FACE_SIZE
            )

            if aligned_crop is None or aligned_crop.size == 0:
                continue

            # 4. Check Crop Quality (Blur, Head Pose, Low Res)
            is_valid, reason, quality_metrics = evaluate_face_quality(
                face_img=aligned_crop,
                landmarks=matching_raw["landmarks"],
                min_resolution=self.config.MIN_FACE_RESOLUTION,
                blur_threshold=self.config.BLUR_THRESHOLD,
                yaw_limit=self.config.YAW_LIMIT,
                pitch_limit=self.config.PITCH_LIMIT
            )

            # Skip prediction for this frame if quality is poor, keep previous tracking state
            run_inference = is_valid and (frame_counter % frame_skip == 0)

            if run_inference:
                # 5. Preprocessing & Normalization
                gamma_corrected = adjust_gamma(aligned_crop, gamma=self.config.GAMMA)
                normalized_face = apply_clahe(
                    gamma_corrected, 
                    clip_limit=self.config.CLAHE_CLIP_LIMIT,
                    tile_grid_size=self.config.CLAHE_TILE_GRID_SIZE
                )
                
                # Convert to tensor [1, 3, 224, 224]
                face_tensor = preprocess_for_model(normalized_face, target_size=self.config.FACE_SIZE)

                # 6. Model Prediction (8-class probabilities)
                probs8 = self.model.predict_raw_probabilities(face_tensor)
                
                # Scale probabilities to 0-100%
                probs8_percent = [float(p) * 100.0 for p in probs8]

                # Map 8-class to 7-class format
                mapped_probs = map_probabilities_to_api(probs8_percent)

                # 7. Apply EMA Smoothing
                face.smoothed_probabilities = smooth_probabilities_ema(
                    prev_probs=face.smoothed_probabilities,
                    new_probs=mapped_probs,
                    alpha=self.config.EMA_ALPHA
                )

                # Find dominant emotion from smoothed probabilities
                dominant_emotion = max(face.smoothed_probabilities, key=face.smoothed_probabilities.get)
                confidence = face.smoothed_probabilities[dominant_emotion]

                # 8. Confidence Lock & Cooldown Logic
                # If a new expression is highly confident, lock it and reset cooldown
                if confidence >= self.config.CONFIDENCE_LOCK_THRESHOLD:
                    face.locked_emotion = dominant_emotion
                    face.locked_confidence = confidence
                    face.cooldown_counter = self.config.COOLDOWN_FRAMES
                    
                    face.current_emotion = dominant_emotion
                    face.confidence = confidence
                else:
                    # If cooldown is active, hold the locked state
                    if face.cooldown_counter > 0:
                        face.cooldown_counter -= 1
                        face.current_emotion = face.locked_emotion
                        face.confidence = face.locked_confidence
                    else:
                        # Cooldown expired, use current smoothed predictions
                        face.current_emotion = dominant_emotion
                        face.confidence = confidence
            else:
                # Decay cooldown even if we skipped inference
                if face.cooldown_counter > 0:
                    face.cooldown_counter -= 1

            # Append current active tracking values
            active_predictions.append({
                "id": face.face_id,
                "bbox": face.bbox,
                "emotion": face.current_emotion,
                "confidence": face.confidence
            })

            # 9. Draw Overlays (Styled Teal Box & Label)
            if draw_overlays:
                x, y, w, h = face.bbox
                # Teal bounding box (BGR: (230, 216, 0))
                cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (230, 216, 0), 2)
                
                # Check confidence limit
                from backend.config import CONFIDENCE_THRESHOLD
                display_emotion = face.current_emotion
                if face.confidence < CONFIDENCE_THRESHOLD:
                    display_emotion = "Emotion Uncertain"
                
                label = f"ID:{face.face_id} {display_emotion} ({int(face.confidence)}%)"
                
                # Bounding box label header bar
                bar_height = 30
                cv2.rectangle(annotated_frame, (x, y - bar_height), (x + w, y), (230, 216, 0), cv2.FILLED)
                cv2.putText(
                    annotated_frame, 
                    label, 
                    (x + 6, y - 8), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.55, 
                    (0, 0, 0), 
                    2, 
                    cv2.LINE_AA
                )

        return annotated_frame, active_predictions

    def process_frame_as_dicts(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Processes a static image (for /predict-image upload endpoint).
        Does NOT apply tracking or temporal EMA smoothing.
        
        Returns:
            List of dictionaries matching schemas.PredictionResponse
        """
        if frame is None or frame.size == 0:
            return []

        raw_detections = self.detector.detect_faces_raw(frame)
        results = []

        for det in raw_detections:
            bbox = det["bbox"]
            landmarks = det["landmarks"]
            
            # Align and Crop
            aligned_crop = align_and_crop_face(
                frame=frame,
                landmarks=landmarks,
                bbox=bbox,
                target_size=self.config.FACE_SIZE
            )
            
            if aligned_crop is None or aligned_crop.size == 0:
                continue

            # Illumination normalization
            gamma_corrected = adjust_gamma(aligned_crop, gamma=self.config.GAMMA)
            normalized_face = apply_clahe(
                gamma_corrected, 
                clip_limit=self.config.CLAHE_CLIP_LIMIT,
                tile_grid_size=self.config.CLAHE_TILE_GRID_SIZE
            )

            # Standard model tensor preprocessing
            face_tensor = preprocess_for_model(normalized_face, target_size=self.config.FACE_SIZE)

            # Predict
            probs8 = self.model.predict_raw_probabilities(face_tensor)
            probs8_percent = [float(p) * 100.0 for p in probs8]
            
            # Map labels
            mapped_probs = map_probabilities_to_api(probs8_percent)
            
            # Determine dominant emotion for static image
            dominant_emotion = max(mapped_probs, key=mapped_probs.get)
            confidence = mapped_probs[dominant_emotion]

            results.append({
                "face_detected": True,
                "bbox": bbox,
                "emotion": dominant_emotion,
                "confidence": confidence,
                "probabilities": mapped_probs
            })

        return results
