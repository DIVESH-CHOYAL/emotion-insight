# Advanced Emotion Engine (Version 2.1)

This module provides high-speed, robust facial emotion recognition and tracking.

## Module Pipeline Flow
1. **Face Detection**: Uses MediaPipe Tasks short-range face detection.
2. **Face Alignment**: Eye landmark based affine roll correction.
3. **Face Quality Checks**: Laplician variance blur detection and geometric head pose boundary estimation.
4. **Illumination Normalization**: Gamma Correction + L-channel CLAHE processing.
5. **ONNX Inference**: Runs the AffectNet 8-class pre-trained model `emotion_hsemotion_b0.onnx`.
6. **Multi-face Tracking**: Centroid matching and tracking history mapping.
7. **Smoothing & Post-processing**: Exponential Moving Average (EMA) smoothing and state machine confidence locking.

## Mapped Outputs
HSEmotion 8-class outputs are converted to the 7 dashboard required standard emotions (Neutral, Happy, Sad, Angry, Fear, Surprise, Disgust) by folding Contempt into Neutral.
