import cv2
import collections
import threading
import time
import logging
import urllib.request
from typing import Generator, Optional, Tuple, Dict, Any
import numpy as np

from backend import config
from backend.services.detector import FaceDetector
from backend.services.predictor import EmotionPredictor
from backend.services.utils import EmotionSmoother, BoundingBoxSmoother

logger = logging.getLogger("backend.services.camera")


class MjpegReader:
    """
    Reads JPEG frames from a multipart MJPEG HTTP stream (e.g. DroidCam WiFi).
    Works where cv2.VideoCapture cannot open the HTTP URL.
    """
    def __init__(self, url: str) -> None:
        self.url = url
        self._stream = None
        self._buf = b""

    def open(self) -> bool:
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            self._stream = urllib.request.urlopen(req, timeout=5)
            self._buf = b""
            logger.info(f"MjpegReader: opened stream {self.url}")
            return True
        except Exception as e:
            logger.error(f"MjpegReader: cannot open {self.url}: {e}")
            return False

    def read(self):
        """Returns (True, frame_ndarray) or (False, None)."""
        try:
            while True:
                chunk = self._stream.read(4096)
                if not chunk:
                    return False, None
                self._buf += chunk
                # Find JPEG start and end markers
                start = self._buf.find(b"\xff\xd8")
                end = self._buf.find(b"\xff\xd9")
                if start != -1 and end != -1 and end > start:
                    jpg_bytes = self._buf[start:end + 2]
                    self._buf = self._buf[end + 2:]
                    arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        return True, frame
        except Exception as e:
            logger.error(f"MjpegReader.read error: {e}")
            return False, None

    def release(self):
        try:
            if self._stream:
                self._stream.close()
                self._stream = None
        except Exception:
            pass

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
        self.emotion_smoother = EmotionSmoother(alpha=config.EMA_ALPHA, min_consecutive=2)
        self.bbox_smoother = BoundingBoxSmoother(window_size=5)
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.mjpeg_reader: Optional[MjpegReader] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        self._frame_lock = threading.Lock()
        
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
        Prefers CAMERA_URL (e.g. DroidCam WiFi) over CAMERA_INDEX if set.
        """
        with self._lock:
            if self.is_running:
                logger.info("Camera is already running.")
                return True
            
            camera_url = getattr(config, 'CAMERA_URL', None)
            camera_index = config.CAMERA_INDEX

            if camera_url:
                logger.info(f"Starting VideoCamera with MJPEG URL: {camera_url}")
                reader = MjpegReader(camera_url)
                if not reader.open():
                    logger.error(f"Could not open MJPEG stream: {camera_url}")
                    self.is_running = False
                    return False
                self.mjpeg_reader = reader
                self.cap = None
            else:
                logger.info(f"Starting VideoCamera with index {camera_index}...")
                if camera_index == 0:
                    self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                    if not self.cap.isOpened():
                        self.cap = cv2.VideoCapture(camera_index)
                else:
                    self.cap = cv2.VideoCapture(camera_index)
                    if not self.cap.isOpened():
                        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                
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
        Stops the camera background reader and releases the webcam or MJPEG stream.
        """
        with self._lock:
            if not self.is_running:
                return
            logger.info("Stopping VideoCamera...")
            self.is_running = False
            
            if self.thread:
                self.thread.join(timeout=2.0)
                self.thread = None
                
            if self.cap:
                self.cap.release()
                self.cap = None

            if self.mjpeg_reader:
                self.mjpeg_reader.release()
                self.mjpeg_reader = None
                
            self.latest_frame = None
            logger.info("VideoCamera stopped and released.")

    def _capture_loop(self) -> None:
        """
        Background thread capture and process loop.
        Reads from MjpegReader (DroidCam WiFi) or cv2.VideoCapture (local cam).
        """
        frame_times = collections.deque(maxlen=30)
        
        while self.is_running:
            start_time = time.time()
            if self.mjpeg_reader is not None:
                ret, frame = self.mjpeg_reader.read()
            else:
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
        
        if self.frame_counter <= 5:
            avg_bgr = frame.mean(axis=(0, 1))
            logger.info(f"Frame {self.frame_counter} stats - Shape: {frame.shape}, Avg BGR: {avg_bgr}")
            
        # Face detection (returns BGR crop and original bounding box)
        faces = self.detector.detect_faces(frame)
        self.faces_count = len(faces)
        
        if self.faces_count > 0:
            # Select primary (largest) face
            primary_face = max(faces, key=lambda f: f[0][2] * f[0][3])
            (x, y, w, h), aligned_crop = primary_face
            
            # Smooth bounding box coordinates
            sx, sy, sw, sh = self.bbox_smoother.smooth((x, y, w, h))
            
            # Run prediction every N frames (configured via FRAME_SKIP)
            frame_skip = config.FRAME_SKIP
            if self.frame_counter % frame_skip == 0 or self.current_emotion == "Neutral":
                if aligned_crop is not None and aligned_crop.size > 0:
                    try:
                        raw_probs = self.predictor.predict_probabilities(aligned_crop)
                        self.current_emotion, self.confidence, _ = self.emotion_smoother.process(raw_probs)
                    except Exception as e:
                        logger.error(f"Error during ONNX emotion prediction: {e}")
            
            # Render a modern vibrant teal bounding box (BGR: (230, 216, 0))
            cv2.rectangle(frame, (sx, sy), (sx + sw, sy + sh), (230, 216, 0), 2)
            
            # Apply confidence threshold for overlay display
            display_emotion = self.current_emotion
            if self.confidence < config.CONFIDENCE_THRESHOLD:
                display_emotion = "Emotion Uncertain"
                
            # Draw premium label overlay
            label = f"{display_emotion} ({int(self.confidence)}%)"
            
            # Filled header bar for label
            bar_height = 30
            cv2.rectangle(frame, (sx, sy - bar_height), (sx + sw, sy), (230, 216, 0), cv2.FILLED)
            
            # Label text
            cv2.putText(
                frame, 
                label, 
                (sx + 8, sy - 8), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, 
                (0, 0, 0), 
                2, 
                cv2.LINE_AA
            )
        else:
            self.bbox_smoother.reset()
            # Decay the predicted state back to neutral if no faces are detected
            if self.frame_counter % 5 == 0:
                self.emotion_smoother.reset()
                self.current_emotion = "Neutral"
                self.confidence = 0.0

        with self._frame_lock:
            self.latest_frame = frame.copy()

    def get_frame_bytes(self) -> Optional[bytes]:
        """
        Encodes the latest processed frame to JPEG and returns the bytes.
        """
        with self._frame_lock:
            if self.latest_frame is None:
                return None
            frame_to_encode = self.latest_frame.copy()
        
        ret, jpeg = cv2.imencode('.jpg', frame_to_encode)
        if not ret:
            return None
        return jpeg.tobytes()

    def get_status(self) -> Dict[str, Any]:
        """
        Returns camera status metrics.
        """
        status_str = "Running" if self.is_running else "Stopped"
        
        emotion = self.current_emotion
        if self.is_running and self.confidence < config.CONFIDENCE_THRESHOLD:
            emotion = "Emotion Uncertain"
            
        return {
            "camera": status_str,
            "emotion": emotion if self.is_running else "—",
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
