from typing import Dict

def smooth_probabilities_ema(
    prev_probs: Dict[str, float], 
    new_probs: Dict[str, float], 
    alpha: float = 0.3
) -> Dict[str, float]:
    """
    Applies Exponential Moving Average (EMA) to probability dictionary mapping.
    prev_probs and new_probs map emotion keys (e.g., Happy, Sad, Neutral) to percentage float values (0-100).
    """
    if not prev_probs:
        return new_probs.copy()

    smoothed = {}
    for key in new_probs.keys():
        p_prev = prev_probs.get(key, 0.0)
        p_new = new_probs[key]
        smoothed[key] = alpha * p_new + (1.0 - alpha) * p_prev

    # Normalize to ensure they sum to exactly 100.0%
    total = sum(smoothed.values())
    if total > 0:
        for key in smoothed.keys():
            smoothed[key] = (smoothed[key] / total) * 100.0
            
    return smoothed
