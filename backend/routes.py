import os
import uuid
import logging
import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any

from backend import schemas
from backend.services.camera import VideoCamera

logger = logging.getLogger("backend.routes")

router = APIRouter(tags=["Emotion Detection"])

# Camera instance singleton
camera = VideoCamera()

@router.get(
    "/health",
    response_model=schemas.HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the status of the FastAPI server to verify it is running."
)
def health_check() -> schemas.HealthResponse:
    return schemas.HealthResponse(status="running")

@router.post(
    "/predict-image",
    response_model=schemas.PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Emotion from Image",
    description="Uploads an image, detects the primary face, runs emotion recognition, and returns predictions with probability scores."
)
async def predict_image(file: UploadFile = File(...)) -> schemas.PredictionResponse:
    try:
        filename = file.filename or "uploaded_image.png"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            logger.warning(f"Invalid file format uploaded: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Unsupported image format. Use JPG, PNG or WEBP."
            )

        # Read file contents
        content = await file.read()
        
        # Save image to uploads folder for record keeping
        current_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_dir = os.path.join(current_dir, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        upload_path = os.path.join(uploads_dir, f"{uuid.uuid4()}{ext}")
        with open(upload_path, "wb") as f:
            f.write(content)
        logger.info(f"Saved uploaded image to {upload_path}")

        # Decode image using OpenCV
        np_arr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            logger.warning("Uploaded file could not be decoded as image.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Could not decode image."
            )

        # Run Advanced Emotion Engine detection and prediction
        predictions = camera.emotion_engine.process_frame_as_dicts(img)
        if not predictions:
            logger.info("No faces detected in the uploaded image.")
            return schemas.PredictionResponse(face_detected=False)

        # Select the primary (largest) face based on bounding box size
        primary = max(predictions, key=lambda p: p["bbox"][2] * p["bbox"][3])
        x, y, w, h = primary["bbox"]
        emotion = primary["emotion"]
        confidence = primary["confidence"]
        probabilities = primary["probabilities"]
        
        # Apply adaptive confidence threshold
        from backend.config import CONFIDENCE_THRESHOLD
        if confidence < CONFIDENCE_THRESHOLD:
            emotion = "Emotion Uncertain"
        
        logger.info(f"Image prediction successful: {emotion} ({confidence:.1f}%)")
        return schemas.PredictionResponse(
            face_detected=True,
            emotion=emotion,
            confidence=round(confidence, 1),
            bounding_box=[int(x), int(y), int(w), int(h)],
            probabilities=probabilities
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error during predict_image:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Prediction failure: {str(e)}"
        )


@router.get(
    "/video-feed",
    summary="Video Feed Stream",
    description="Returns the live MJPEG webcam stream with face detection overlays."
)
def video_feed() -> StreamingResponse:
    if not camera.is_running:
        started = camera.start()
        if not started:
            logger.error("Webcam stream requested but camera is unavailable.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Camera is currently unavailable."
            )
            
    return StreamingResponse(
        camera.gen_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get(
    "/camera-status",
    response_model=schemas.CameraStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Camera Status",
    description="Returns the real-time status of the webcam stream including current emotion, confidence, FPS, and face count."
)
def camera_status() -> schemas.CameraStatusResponse:
    status_data = camera.get_status()
    # Handle the '—' placeholder for emotion
    emotion = status_data["emotion"]
    if emotion == "—":
        emotion = "Neutral"
        
    return schemas.CameraStatusResponse(
        camera=status_data["camera"],
        emotion=emotion,
        confidence=status_data["confidence"],
        fps=status_data["fps"],
        faces=status_data["faces"]
    )

@router.post(
    "/camera/start",
    status_code=status.HTTP_200_OK,
    summary="Start Camera",
    description="Explicitly turns on the webcam and starts frame capture loop."
)
def start_camera() -> Dict[str, str]:
    success = camera.start()
    if not success:
        logger.error("Failed to explicitly start camera.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Failed to start the camera. It might be in use or disconnected."
        )
    return {"status": "success", "message": "Camera started."}

@router.post(
    "/camera/stop",
    status_code=status.HTTP_200_OK,
    summary="Stop Camera",
    description="Explicitly turns off the webcam and releases resources."
)
def stop_camera() -> Dict[str, str]:
    camera.stop()
    return {"status": "success", "message": "Camera stopped."}

@router.get(
    "/camera/snapshot",
    summary="Capture Camera Snapshot",
    description="Captures a single JPEG frame from the active webcam feed."
)
def camera_snapshot() -> StreamingResponse:
    import io
    frame_bytes = camera.get_frame_bytes()
    if frame_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Camera frame not available. Ensure the camera is running."
        )
    return StreamingResponse(io.BytesIO(frame_bytes), media_type="image/jpeg")

@router.get(
    "/settings",
    response_model=schemas.SettingsResponse,
    summary="Get Current Camera Settings",
    description="Returns the currently active camera index, confidence threshold, and bounding box preference."
)
def get_settings() -> Dict[str, Any]:
    from backend import config
    return {
        "status": "success",
        "camera_index": config.CAMERA_INDEX,
        "confidence_threshold": config.CONFIDENCE_THRESHOLD,
        "draw_bounding_boxes": getattr(config, 'DRAW_BOUNDING_BOXES', True)
    }

@router.post(
    "/settings",
    response_model=schemas.SettingsResponse,
    summary="Update Camera Settings",
    description="Updates the camera index, confidence threshold, and bounding box preference. Persists to .env and releases the active camera if running."
)
def update_settings(settings: schemas.SettingsRequest) -> Dict[str, Any]:
    from backend import config
    
    # 1. Update runtime configuration
    config.CAMERA_INDEX = settings.camera_index
    config.CONFIDENCE_THRESHOLD = settings.confidence_threshold
    config.DRAW_BOUNDING_BOXES = settings.draw_bounding_boxes
    
    # 2. Persist back to backend/.env
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(current_dir, ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
                
        new_lines = []
        has_cam = False
        has_thresh = False
        has_bbox = False
        for line in lines:
            if line.strip().startswith("CAMERA_INDEX="):
                new_lines.append(f"CAMERA_INDEX={settings.camera_index}\n")
                has_cam = True
            elif line.strip().startswith("CONFIDENCE_THRESHOLD="):
                new_lines.append(f"CONFIDENCE_THRESHOLD={settings.confidence_threshold}\n")
                has_thresh = True
            elif line.strip().startswith("DRAW_BOUNDING_BOXES="):
                new_lines.append(f"DRAW_BOUNDING_BOXES={'true' if settings.draw_bounding_boxes else 'false'}\n")
                has_bbox = True
            else:
                new_lines.append(line)
                
        if not has_cam:
            new_lines.append(f"CAMERA_INDEX={settings.camera_index}\n")
        if not has_thresh:
            new_lines.append(f"CONFIDENCE_THRESHOLD={settings.confidence_threshold}\n")
        if not has_bbox:
            new_lines.append(f"DRAW_BOUNDING_BOXES={'true' if settings.draw_bounding_boxes else 'false'}\n")
            
        with open(env_path, "w") as f:
            f.writelines(new_lines)
        logger.info("Persisted new settings to .env file successfully.")
    except Exception as e:
        logger.error(f"Failed to persist settings to .env file: {e}")
        
    # 3. Stop the active camera so it reopens with the new device next time
    if camera.is_running:
        logger.info("Stopping camera to apply new device configuration...")
        camera.stop()
        
    return {
        "status": "success",
        "camera_index": config.CAMERA_INDEX,
        "confidence_threshold": config.CONFIDENCE_THRESHOLD,
        "draw_bounding_boxes": config.DRAW_BOUNDING_BOXES
    }
