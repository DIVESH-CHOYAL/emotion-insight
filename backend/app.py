import os
import logging
from logging.handlers import RotatingFileHandler
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.routes import router as api_router, camera

# Ensure logs directory exists
current_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(current_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, "app.log")

# Configure logging to write to both file and console
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger("backend.app")

app = FastAPI(
    title="EmotionSense AI Backend",
    description="Production-ready FastAPI backend for Facial Emotion Recognition (FER) with prediction smoothing.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS restricted to frontend development origins
logger.info(f"Configuring CORS with allowed origins: {config.ALLOWED_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers for clean JSON responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception occurred on path {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Include API endpoints
app.include_router(api_router)

@app.on_event("startup")
def startup_event():
    logger.info("EmotionSense AI Backend successfully started.")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down EmotionSense AI Backend...")
    camera.stop()
    logger.info("Cleanup complete.")

if __name__ == "__main__":
    ssl_key = getattr(config, "SSL_KEYFILE", None)
    ssl_cert = getattr(config, "SSL_CERTFILE", None)
    
    if ssl_key and ssl_cert:
        logger.info(f"Starting server with HTTPS (SSL Enabled) using cert: {ssl_cert}")
        uvicorn.run(
            "backend.app:app", 
            host=config.HOST, 
            port=config.PORT, 
            reload=True, 
            ssl_keyfile=ssl_key, 
            ssl_certfile=ssl_cert
        )
    else:
        logger.info("Starting server with HTTP (SSL Disabled)")
        uvicorn.run("backend.app:app", host=config.HOST, port=config.PORT, reload=True)
