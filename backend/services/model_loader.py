import os
import logging
from typing import Optional
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D

from backend import config

logger = logging.getLogger("backend.services.model_loader")

class ModelLoader:
    _model: Optional[Sequential] = None

    @classmethod
    def get_model(cls) -> Sequential:
        if cls._model is None:
            cls._model = cls._build_and_load_model()
        return cls._model

    @classmethod
    def _build_and_load_model(cls) -> Sequential:
        weights_path = config.MODEL_PATH
        logger.info(f"Initializing and loading emotion model from {weights_path}...")
        
        # Build the model architecture matching the trained weights
        model = Sequential()

        model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48, 48, 1)))
        model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))

        model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))

        model.add(Flatten())
        model.add(Dense(1024, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(7, activation='softmax'))

        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Model weights file not found at {weights_path}")

        # Load weights
        model.load_weights(weights_path)
        logger.info("Emotion model weights loaded successfully.")
        return model
