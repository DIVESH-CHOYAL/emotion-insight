import cv2
import numpy as np

def adjust_gamma(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
    """
    Applies gamma correction to adjust brightness.
    gamma < 1.0 brightens, gamma > 1.0 darkens.
    """
    if gamma == 1.0 or image is None or image.size == 0:
        return image

    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) on the L channel of LAB color space.
    Performs illumination normalization without distorting color profiles.
    """
    if image is None or image.size == 0:
        return image

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def preprocess_for_model(face_img: np.ndarray, target_size: int = 224) -> np.ndarray:
    """
    Converts a face crop BGR image to the standardized input format required by the HSEmotion ONNX model:
    - RGB color conversion
    - Scaling / Resizing to target_size x target_size
    - Normalization: division by 255, subtracting ImageNet mean, dividing by ImageNet std
    - Transposing to (1, 3, target_size, target_size) channel-first float32 tensor
    """
    if face_img is None or face_img.size == 0:
        return np.zeros((1, 3, target_size, target_size), dtype=np.float32)

    # 1. Convert BGR to RGB (HSEmotion expects RGB input)
    rgb_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

    # 2. Resize
    resized = cv2.resize(rgb_img, (target_size, target_size))

    # 3. Normalize values [0.0, 1.0]
    normalized = resized.astype(np.float32) / 255.0

    # 4. Standard ImageNet Mean and Std normalizations
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    
    normalized = (normalized - mean) / std

    # 5. Transpose HWC -> CHW, and add batch dimension: [1, C, H, W]
    tensor = normalized.transpose(2, 0, 1)  # Shape: (3, H, W)
    tensor = np.expand_dims(tensor, axis=0)  # Shape: (1, 3, H, W)
    
    return tensor.astype(np.float32)
