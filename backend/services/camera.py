import cv2
import collections
import threading
import time
import logging
from typing import Generator, Optional, Tuple, Dict, Any
import numpy as np

from backend import config
from backend.services.detector import FaceDetector
from backend.services.predictor import EmotionPredictor
from backend.services.utils import EmotionSmoother, BoundingBoxSmoother

logger = logging.getLogger("backend.services.camera")

class VideoCamera:
    _instance: Optional['VideoCamera'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(VideoCamera, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        
        self.detector = FaceDetector()
        self.predictor = EmotionPredictor()
        self.emotion_smoother = EmotionSmoother()
        self.bbox_smoother = BoundingBoxSmoother()
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # State metrics
        self.current_emotion = "Neutral"
        self.confidence = 0.0
        self.faces_count = 0
        self.fps = 0.0
        
        # Internal state for background worker
        self.latest_frame: Optional[np.ndarray] = None
        self.frame_counter = 0

    def start(self) -> bool:
        """
        Starts the webcam and the background frame reader thread.
        """
        with self._lock:
            if self.is_running:
                logger.info("Camera is already running.")
                return True
            
            camera_index = config.CAMERA_INDEX
            logger.info(f"Starting VideoCamera with index {camera_index}...")
            
            # Try camera index with DirectShow for fast startup on Windows
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback without CAP_DSHOW
                self.cap = cv2.VideoCapture(camera_index)
                if not self.cap.isOpened():
                    logger.error(f"Webcam (index {camera_index}) could not be opened.")
                    self.is_running = False
                    return False
            
            self.is_running = True
            # Reset smoothers
            self.emotion_smoother.reset()
            self.bbox_smoother.reset()
            
            self.current_emotion = "Neutral"
            self.confidence = 0.0
            self.faces_count = 0
            self.fps = 0.0
            self.latest_frame = None
            self.frame_counter = 0
            
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logger.info("VideoCamera background thread started successfully.")
            return True

    def stop(self) -> None:
        """
        Stops the camera background reader and releases the webcam.
        """
        with self._lock:
            if not self.is_running:
                return
            logger.info("Stopping VideoCamera...")
            self.is_running = False
            
            if self.thread:
                self.thread.join(timeout=1.0)
                self.thread = None
                
            if self.cap:
                self.cap.release()
                self.cap = None
                
            self.latest_frame = None
            logger.info("VideoCamera stopped and released.")

    def _capture_loop(self) -> None:
        """
        Background thread capture and process loop.
        """
        frame_times = collections.deque(maxlen=30)
        
        while self.is_running:
            start_time = time.time()
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.warning("Failed to grab frame from camera.")
                time.sleep(0.03)
                continue
            
            # FPS calculation
            frame_times.append(start_time)
            if len(frame_times) > 1:
                self.fps = round(len(frame_times) / (frame_times[-1] - frame_times[0]), 1)
            else:
                self.fps = 30.0

            # Process frame
            try:
                self._process_frame(frame)
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
            
            # Control loop speed roughly matching 30fps
            elapsed = time.time() - start_time
            sleep_time = max(0.0, 0.033 - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _process_frame(self, frame: np.ndarray) -> None:
        self.frame_counter += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Face detection
        faces = self.detector.detect_faces(gray)
        self.faces_count = len(faces)
        
        if self.faces_count > 0:
            primary_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = primary_face
            
            # Smooth bounding box
            sx, sy, sw, sh = self.bbox_smoother.smooth(primary_face)
            
            # Run CNN inference according to configuration
            frame_skip = config.FRAME_SKIP
            if self.frame_counter % frame_skip == 0 or self.current_emotion == "Neutral":
                img_h, img_w = gray.shape
                cx = max(0, x)
                cy = max(0, y)
                cw = min(w, img_w - cx)
                ch = min(h, img_h - cy)
                
                if cw > 0 and ch > 0:
                    roi_gray = gray[cy:cy+ch, cx:cx+cw]
                    try:
                        emotion, raw_confidence = self.predictor.predict_emotion(roi_gray)
                        self.current_emotion, self.confidence = self.emotion_smoother.add_prediction(
                            emotion, raw_confidence
                        )
                    except Exception as e:
                        logger.error(f"Error during CNN emotion prediction: {e}")
            
            # Draw smoothed bounding box (Blue rectangle)
            cv2.rectangle(frame, (sx, sy - 50), (sx + sw, sy + sh + 10), (255, 0, 0), 2)
            
            # Draw label
            label = f"{self.current_emotion} ({int(self.confidence)}%)"
            cv2.putText(
                frame, 
                label, 
                (sx + 10, sy - 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.8, 
                (255, 255, 255), 
                2, 
                cv2.LINE_AA
            )
        else:
            self.bbox_smoother.reset()
            self.faces_count = 0
            if self.frame_counter % 10 == 0:
                self.current_emotion = "Neutral"
                self.confidence = 0.0

        self.latest_frame = frame

    def get_frame_bytes(self) -> Optional[bytes]:
        """
        Encodes the latest processed frame to JPEG and returns the bytes.
        """
        if self.latest_frame is None:
            return None
        
        ret, jpeg = cv2.imencode('.jpg', self.latest_frame)
        if not ret:
            return None
        return jpeg.tobytes()

    def get_status(self) -> Dict[str, Any]:
        """
        Returns camera status metrics.
        """
        status_str = "Running" if self.is_running else "Stopped"
        return {
            "camera": status_str,
            "emotion": self.current_emotion if self.is_running else "—",
            "confidence": round(self.confidence, 1) if self.is_running else 0.0,
            "fps": round(self.fps, 1) if self.is_running else 0.0,
            "faces": self.faces_count if self.is_running else 0
        }

    def gen_frames(self) -> Generator[bytes, None, None]:
        """
        MJPEG stream generator yielding multipart frames.
        """
        while self.is_running:
            frame_bytes = self.get_frame_bytes()
            if frame_bytes is None:
                time.sleep(0.03)
                continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.033)
