import os
from dotenv import load_dotenv

# Load local environment variables from .env file
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()  # Fallback to default search

# Paths
# Default to models/ relative to backend/ root
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(current_dir, "models", "emotion_model.onnx"))
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
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "70.0"))
except ValueError:
    CONFIDENCE_THRESHOLD = 70.0

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

# CORS Allowed Origins (list of strings)
origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080,https://localhost:3000,https://localhost:5173,https://localhost:8080")
ALLOWED_ORIGINS = [o.strip() for o in origins_raw.split(",") if o.strip()]

# SSL Configuration
SSL_KEYFILE = os.path.join(current_dir, "key.pem")
SSL_CERTFILE = os.path.join(current_dir, "cert.pem")

if not os.path.exists(SSL_KEYFILE) or not os.path.exists(SSL_CERTFILE):
    SSL_KEYFILE = None
    SSL_CERTFILE = None

