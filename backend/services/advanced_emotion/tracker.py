import numpy as np
from typing import Dict, List, Tuple, Any

class TrackedFace:
    def __init__(self, face_id: int, bbox: Tuple[int, int, int, int]):
        self.face_id = face_id
        self.bbox = bbox  # [x, y, w, h]
        self.centroid = (bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2)
        
        self.disappeared_count = 0
        
        # State values
        self.smoothed_probabilities = None  # To be initialized upon first prediction
        self.current_emotion = "Neutral"
        self.confidence = 0.0
        
        # Cooldown state machine for expression lock
        self.cooldown_counter = 0
        self.locked_emotion = "Neutral"
        self.locked_confidence = 0.0

    def update(self, bbox: Tuple[int, int, int, int]):
        self.bbox = bbox
        self.centroid = (bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2)
        self.disappeared_count = 0

class FaceTracker:
    def __init__(self, max_disappeared: int = 10, max_distance: float = 100.0):
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        
        self.next_face_id = 0
        self.tracked_faces: Dict[int, TrackedFace] = {}

    def register(self, bbox: Tuple[int, int, int, int]) -> TrackedFace:
        face = TrackedFace(self.next_face_id, bbox)
        self.tracked_faces[self.next_face_id] = face
        self.next_face_id += 1
        return face

    def deregister(self, face_id: int):
        if face_id in self.tracked_faces:
            del self.tracked_faces[face_id]

    def update(self, detected_bboxes: List[Tuple[int, int, int, int]]) -> List[TrackedFace]:
        """
        Updates tracked faces based on detected bounding boxes.
        Returns a list of updated TrackedFace objects matching the detected bboxes.
        """
        # If no faces were detected, increment disappeared counter and deregister if needed
        if len(detected_bboxes) == 0:
            for face_id in list(self.tracked_faces.keys()):
                self.tracked_faces[face_id].disappeared_count += 1
                if self.tracked_faces[face_id].disappeared_count > self.max_disappeared:
                    self.deregister(face_id)
            return []

        # If no faces are currently tracked, register all detections
        if len(self.tracked_faces) == 0:
            active_faces = []
            for bbox in detected_bboxes:
                face = self.register(bbox)
                active_faces.append(face)
            return active_faces

        # Extract current track IDs and centroids
        tracked_ids = list(self.tracked_faces.keys())
        tracked_centroids = np.array([self.tracked_faces[fid].centroid for fid in tracked_ids])

        # Extract detected centroids
        detected_centroids = np.array([(bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2) for bbox in detected_bboxes])

        # Compute Euclidean distance between all tracked and detected centroids
        # Shape: (len(tracked_centroids), len(detected_centroids))
        dists = np.linalg.norm(tracked_centroids[:, np.newaxis] - detected_centroids, axis=2)

        # Match closest centroids
        # Find minimum distance along columns (detections) and rows (tracks)
        row_indices = dists.min(axis=1).argsort()
        col_indices = dists.argmin(axis=1)[row_indices]

        used_rows = set()
        used_cols = set()

        matches = []
        for r, c in zip(row_indices, col_indices):
            if r in used_rows or c in used_cols:
                continue

            # Don't match if distance exceeds threshold
            if dists[r, c] > self.max_distance:
                continue

            face_id = tracked_ids[r]
            face = self.tracked_faces[face_id]
            face.update(detected_bboxes[c])
            matches.append((c, face))
            
            used_rows.add(r)
            used_cols.add(c)

        # Handle remaining unmatched rows (missing tracks)
        unmatched_rows = set(range(0, dists.shape[0])).difference(used_rows)
        for r in unmatched_rows:
            face_id = tracked_ids[r]
            self.tracked_faces[face_id].disappeared_count += 1
            if self.tracked_faces[face_id].disappeared_count > self.max_disappeared:
                self.deregister(face_id)

        # Handle remaining unmatched columns (new detections)
        unmatched_cols = set(range(0, dists.shape[1])).difference(used_cols)
        matched_dict = dict(matches)
        
        final_list = []
        for c, bbox in enumerate(detected_bboxes):
            if c in matched_dict:
                final_list.append(matched_dict[c])
            else:
                face = self.register(bbox)
                final_list.append(face)

        return final_list
