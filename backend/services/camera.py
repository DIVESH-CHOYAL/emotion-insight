import cv2
import collections
import threading
import time
import logging
import urllib.request
from typing import Generator, Optional, Tuple, Dict, Any
import numpy as np

from backend import config
from backend.services.advanced_emotion import EmotionEngine

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
        
        self.emotion_engine = EmotionEngine()
        
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
        Starts the local webcam and the background frame reader thread.
        Tries CAMERA_INDEX first, then auto-falls back to the other index.
        """
        with self._lock:
            if self.is_running:
                logger.info("Camera is already running.")
                return True

            camera_index = config.CAMERA_INDEX
            logger.info(f"Starting VideoCamera with index {camera_index}...")

            # Try DirectShow backend first (Windows), then default
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(camera_index)

            # Auto-fallback: try the other index if still not open
            if not self.cap.isOpened():
                fallback = 1 if camera_index == 0 else 0
                logger.warning(f"Index {camera_index} failed. Trying fallback index {fallback}...")
                self.cap = cv2.VideoCapture(fallback, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(fallback)

            if not self.cap.isOpened():
                logger.error("No webcam could be opened on index 0 or 1.")
                self.cap = None
                self.is_running = False
                return False

            self.mjpeg_reader = None
            self.is_running = True

            # Safe tracker reset
            try:
                tracker_cls = type(self.emotion_engine.tracker)
                eng_cfg = self.emotion_engine.config
                self.emotion_engine.tracker = tracker_cls(
                    max_disappeared=eng_cfg.TRACKER_MAX_DISAPPEARED,
                    max_distance=eng_cfg.TRACKER_MAX_DISTANCE,
                )
            except Exception as e:
                logger.warning(f"Could not reset tracker: {e}")

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
            
        # Run Advanced Emotion Engine detection, tracking, and prediction
        draw_bbox = getattr(config, 'DRAW_BOUNDING_BOXES', True)
        annotated_frame, face_predictions = self.emotion_engine.process_frame(
            frame=frame,
            draw_overlays=draw_bbox,
            frame_counter=self.frame_counter,
            frame_skip=config.FRAME_SKIP
        )
        
        self.faces_count = len(face_predictions)
        if self.faces_count > 0:
            # Use the primary (largest) face for global camera status dashboard statistics
            primary = max(face_predictions, key=lambda f: f["bbox"][2] * f["bbox"][3])
            self.current_emotion = primary["emotion"]
            self.confidence = primary["confidence"]
        else:
            self.current_emotion = "Neutral"
            self.confidence = 0.0
            
        with self._frame_lock:
            self.latest_frame = annotated_frame.copy()

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
