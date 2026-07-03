from collections import deque
from typing import List, Tuple, Dict, Optional
from backend import config

class EmotionSmoother:
    """
    Stabilizes predictions by:
    1. Applying Exponential Moving Average (EMA) to class probabilities.
    2. Enforcing consecutive frame confirmation before changing the dominant emotion.
    """
    def __init__(self, alpha: float = 0.3, min_consecutive: int = 3) -> None:
        self.alpha = alpha
        self.min_consecutive = min_consecutive
        
        self.smoothed_probs: Dict[str, float] = {}
        self.current_emotion: str = "Neutral"
        self.current_confidence: float = 0.0
        
        # Confirmation tracking
        self.pending_emotion: Optional[str] = None
        self.consecutive_count: int = 0

    def process(self, raw_probs: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        """
        Processes a raw frame's prediction probabilities, updates the EMA state,
        runs consecutive frame confirmation, and returns:
        (stable_dominant_emotion, stable_confidence, smoothed_probabilities_dict)
        """
        if not raw_probs:
            return self.current_emotion, self.current_confidence, self.smoothed_probs

        # 1. Apply EMA smoothing
        if not self.smoothed_probs:
            self.smoothed_probs = {k: v for k, v in raw_probs.items()}
        else:
            for k, v in raw_probs.items():
                if k in self.smoothed_probs:
                    self.smoothed_probs[k] = self.alpha * v + (1 - self.alpha) * self.smoothed_probs[k]
                else:
                    self.smoothed_probs[k] = v

        # 2. Get dominant candidate from smoothed probabilities
        dominant_candidate = max(self.smoothed_probs, key=self.smoothed_probs.get)
        confidence_candidate = self.smoothed_probs[dominant_candidate]

        # 3. Apply consecutive frame confirmation
        if dominant_candidate == self.current_emotion:
            # Reset confirmation when candidate matches current stable state
            self.current_confidence = confidence_candidate
            self.pending_emotion = None
            self.consecutive_count = 0
        else:
            if dominant_candidate == self.pending_emotion:
                self.consecutive_count += 1
            else:
                self.pending_emotion = dominant_candidate
                self.consecutive_count = 1

            if self.consecutive_count >= self.min_consecutive:
                # Confirmed switch
                self.current_emotion = dominant_candidate
                self.current_confidence = confidence_candidate
                self.pending_emotion = None
                self.consecutive_count = 0

        return self.current_emotion, self.current_confidence, self.smoothed_probs

    def reset(self) -> None:
        self.smoothed_probs.clear()
        self.current_emotion = "Neutral"
        self.current_confidence = 0.0
        self.pending_emotion = None
        self.consecutive_count = 0


class BoundingBoxSmoother:
    """
    A simple moving average filter to smooth bounding box coordinates
    and eliminate jitter in video rendering.
    """
    def __init__(self, window_size: int = 5) -> None:
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def smooth(self, bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        self.history.append(bbox)
        
        avg_x = int(sum(b[0] for b in self.history) / len(self.history))
        avg_y = int(sum(b[1] for b in self.history) / len(self.history))
        avg_w = int(sum(b[2] for b in self.history) / len(self.history))
        avg_h = int(sum(b[3] for b in self.history) / len(self.history))
        
        return (avg_x, avg_y, avg_w, avg_h)

    def reset(self) -> None:
        self.history.clear()
