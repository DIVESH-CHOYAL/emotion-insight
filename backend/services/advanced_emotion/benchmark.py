import time
import psutil
import os
import numpy as np
import cv2
from .emotion_engine import EmotionEngine

def run_advanced_benchmark():
    print("=== Advanced Emotion Engine Benchmark (Version 2.1) ===")
    
    process = psutil.Process(os.getpid())
    init_mem = process.memory_info().rss / (1024 * 1024)  # MB
    
    start_init = time.time()
    engine = EmotionEngine()
    init_time = (time.time() - start_init) * 1000
    
    post_mem = process.memory_info().rss / (1024 * 1024)  # MB
    mem_overhead = post_mem - init_mem
    
    print(f"Engine initialized in {init_time:.2f} ms")
    print(f"Memory overhead of engine: {mem_overhead:.2f} MB")
    
    # Run mock frame loop (50 frames)
    mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw simple mock face outline to check detector behavior
    cv2.circle(mock_frame, (320, 240), 90, (255, 255, 255), -1)
    
    print("Starting processing profiling (50 frames)...")
    latencies = []
    
    for i in range(50):
        t0 = time.time()
        # Run process frame, skip overlays
        _, preds = engine.process_frame(mock_frame, draw_overlays=False, frame_counter=i, frame_skip=3)
        t1 = time.time()
        latencies.append((t1 - t0) * 1000)
        
    avg_latency = np.mean(latencies)
    max_fps = 1000.0 / avg_latency
    print(f"Average frame processing latency: {avg_latency:.2f} ms")
    print(f"Theoretical Max performance: {max_fps:.1f} FPS")

if __name__ == "__main__":
    run_advanced_benchmark()
