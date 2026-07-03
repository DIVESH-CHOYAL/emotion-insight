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
from backend.services.detector import FaceDetector
from backend.services.predictor import EmotionPredictor

logger = logging.getLogger("backend.routes")

router = APIRouter(tags=["Emotion Detection"])

# Reusable detector and predictor for image uploads
image_detector = FaceDetector()
image_predictor = EmotionPredictor()

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

        # Detect faces (MediaPipe works on color BGR images)
        faces_data = image_detector.detect_faces(img)
        if not faces_data:
            logger.info("No faces detected in the uploaded image.")
            return schemas.PredictionResponse(face_detected=False)

        # Select the primary (largest) face based on bounding box size
        primary_face = max(faces_data, key=lambda f: f[0][2] * f[0][3])
        (x, y, w, h), aligned_crop = primary_face
        
        # Predict using the aligned crop BGR image
        emotion, confidence = image_predictor.predict_emotion(aligned_crop)
        probabilities = image_predictor.predict_probabilities(aligned_crop)
        
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
