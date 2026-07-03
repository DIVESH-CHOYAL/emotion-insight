from collections import Counter
import collections
from typing import List, Tuple, Optional
from backend import config

class EmotionSmoother:
    def __init__(self, window_size: int = 10, confidence_threshold: Optional[float] = None) -> None:
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold if confidence_threshold is not None else config.CONFIDENCE_THRESHOLD
        self.history = collections.deque(maxlen=window_size)
        self.last_stable_emotion: str = "Neutral"
        self.last_stable_confidence: float = 0.0

    def add_prediction(self, emotion: str, confidence: float) -> Tuple[str, float]:
        """
        Adds a new prediction to the history if it passes the confidence threshold.
        Returns the current stable emotion and its average confidence.
        """
        if confidence >= self.confidence_threshold:
            self.history.append((emotion, confidence))
            
        if self.history:
            emotions_in_history = [item[0] for item in self.history]
            counter = Counter(emotions_in_history)
            dominant_emotion, count = counter.most_common(1)[0]
            
            matching_confidences = [item[1] for item in self.history if item[0] == dominant_emotion]
            avg_confidence = sum(matching_confidences) / len(matching_confidences)
            
            self.last_stable_emotion = dominant_emotion
            self.last_stable_confidence = avg_confidence
            
        return self.last_stable_emotion, self.last_stable_confidence

    def get_stable_prediction(self) -> Tuple[str, float]:
        return self.last_stable_emotion, self.last_stable_confidence

    def reset(self) -> None:
        self.history.clear()


class BoundingBoxSmoother:
    def __init__(self, window_size: int = 5) -> None:
        self.window_size = window_size
        self.history = collections.deque(maxlen=window_size)

    def smooth(self, bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """
        Appends the latest bounding box coordinates and returns the average.
        """
        self.history.append(bbox)
        
        avg_x = int(sum(b[0] for b in self.history) / len(self.history))
        avg_y = int(sum(b[1] for b in self.history) / len(self.history))
        avg_w = int(sum(b[2] for b in self.history) / len(self.history))
        avg_h = int(sum(b[3] for b in self.history) / len(self.history))
        
        return (avg_x, avg_y, avg_w, avg_h)

    def reset(self) -> None:
        self.history.clear()
