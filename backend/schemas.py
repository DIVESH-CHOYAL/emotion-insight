from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class HealthResponse(BaseModel):
    status: str = Field(..., example="running", description="Status of the FastAPI server")

class PredictionResponse(BaseModel):
    face_detected: bool = Field(..., description="Flag indicating if a face was detected in the image")
    emotion: Optional[str] = Field(None, example="Happy", description="The predicted dominant emotion")
    confidence: Optional[float] = Field(None, example=95.0, description="Confidence score percentage (0-100)")
    bounding_box: Optional[List[int]] = Field(None, example=[100, 150, 80, 80], description="Bounding box of the face [x, y, w, h]")
    probabilities: Optional[Dict[str, float]] = Field(None, description="Detailed probability breakdown for each emotion class")

class CameraStatusResponse(BaseModel):
    camera: str = Field(..., example="Running", description="Camera status (e.g., Running, Stopped, Error)")
    emotion: str = Field(..., example="Happy", description="Current detected dominant emotion (smoothed)")
    confidence: float = Field(..., example=95.0, description="Average confidence score percentage")
    fps: float = Field(..., example=30.0, description="Frames per second of the capture process")
    faces: int = Field(..., example=1, description="Number of detected faces in the current frame")
