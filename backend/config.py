import os
from dotenv import load_dotenv

# Load local environment variables from .env file (override=True ensures fresh reads on restart)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)

# Paths — default to the HSEmotion ONNX model
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(current_dir, "models", "emotion_hsemotion_b0.onnx"))
CASCADE_PATH = os.getenv("CASCADE_PATH", os.path.join(current_dir, "models", "haarcascade_frontalface_default.xml"))

# Resolve absolute paths if they are specified relatively
if not os.path.isabs(MODEL_PATH):
    MODEL_PATH = os.path.abspath(os.path.join(current_dir, MODEL_PATH))
if not os.path.isabs(CASCADE_PATH):
    CASCADE_PATH = os.path.abspath(os.path.join(current_dir, CASCADE_PATH))

# Camera configs
try:
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
except ValueError:
    CAMERA_INDEX = 0

try:
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "40.0"))
except ValueError:
    CONFIDENCE_THRESHOLD = 40.0

DRAW_BOUNDING_BOXES = os.getenv("DRAW_BOUNDING_BOXES", "true").lower() == "true"

try:
    FRAME_SKIP = int(os.getenv("FRAME_SKIP", "3"))
except ValueError:
    FRAME_SKIP = 3

try:
    EMA_ALPHA = float(os.getenv("EMA_ALPHA", "0.3"))
except ValueError:
    EMA_ALPHA = 0.3

# Server configs
HOST = os.getenv("HOST", "127.0.0.1")
try:
    PORT = int(os.getenv("PORT", "8000"))
except ValueError:
    PORT = 8000

# CORS Allowed Origins — includes all Vite ports (8080 client, 8081 SSR)
origins_raw = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://localhost:8081,"
    "http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080,http://127.0.0.1:8081"
)
ALLOWED_ORIGINS = [o.strip() for o in origins_raw.split(",") if o.strip()]
