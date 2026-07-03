import os

class AdvancedEmotionConfig:
    def __init__(self):
        # Base paths
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.MODEL_PATH = os.path.join(current_dir, "models", "emotion_hsemotion_b0.onnx")
        self.FACE_DETECTOR_PATH = os.path.join(current_dir, "models", "blaze_face_short_range.tflite")

        # MediaPipe Detection Config
        self.MIN_DETECTION_CONFIDENCE = 0.45

        # Preprocessing & Lighting Norm Config
        self.FACE_SIZE = 224
        self.GAMMA = 1.0  # Gamma correction factor (1.0 = no change, < 1.0 = brighten, > 1.0 = darken)
        self.USE_CLAHE = True
        self.CLAHE_CLIP_LIMIT = 2.0
        self.CLAHE_TILE_GRID_SIZE = (8, 8)

        # Quality Check Configs
        self.BLUR_THRESHOLD = 60.0  # Laplacian variance threshold
        self.MIN_FACE_RESOLUTION = 40  # Minimum width/height in pixels

        # Head Pose Limits (estimated from landmark ratios)
        self.YAW_LIMIT = 35.0  # Degrees
        self.PITCH_LIMIT = 30.0  # Degrees

        # Tracking Configs
        self.TRACKER_MAX_DISAPPEARED = 10  # Max frames a face can be missing before being forgotten
        self.TRACKER_MAX_DISTANCE = 100.0  # Max pixel distance for centroid matching

        # Smoothing & State Machine Configs
        self.EMA_ALPHA = 0.3  # Exponential Moving Average weight (lower is smoother, higher is faster)
        self.COOLDOWN_FRAMES = 6  # Frames to hold a high-confidence expression
        self.CONFIDENCE_LOCK_THRESHOLD = 50.0  # Active when confidence exceeds this percentage
