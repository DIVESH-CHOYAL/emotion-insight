from typing import Dict, List

# Output class index to name map for the 8-class HSEmotion model
HSEMOTION_LABELS = {
    0: 'Anger',
    1: 'Contempt',
    2: 'Disgust',
    3: 'Fear',
    4: 'Happiness',
    5: 'Neutral',
    6: 'Sadness',
    7: 'Surprise'
}

# The 7 frontend labels required by the existing React dashboard API
API_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

def map_probabilities_to_api(probs8: List[float]) -> Dict[str, float]:
    """
    Maps 8-class HSEmotion probabilities (percentages 0-100) to the 7-class API format.
    Contempt (index 1) is folded into Neutral (index 5) to maintain full interface compatibility.
    """
    if len(probs8) < 8:
        # Fallback to defaults
        return {label: 0.0 for label in API_LABELS}

    # Map indices:
    # 0: Anger -> Angry
    # 1: Contempt -> (Combined with Neutral)
    # 2: Disgust -> Disgust
    # 3: Fear -> Fear
    # 4: Happiness -> Happy
    # 5: Neutral -> Neutral
    # 6: Sadness -> Sad
    # 7: Surprise -> Surprise
    
    mapped_probs = {
        "Angry": float(probs8[0]),
        "Disgust": float(probs8[2]),
        "Fear": float(probs8[3]),
        "Happy": float(probs8[4]),
        # Combine Contempt and Neutral to fit 7-class contract cleanly
        "Neutral": float(probs8[5]) + float(probs8[1]),
        "Sad": float(probs8[6]),
        "Surprise": float(probs8[7])
    }
    
    return mapped_probs
