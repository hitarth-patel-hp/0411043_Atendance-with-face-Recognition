import face_recognition
import numpy as np
import cv2
from PIL import Image

from utils.db_utils import (
    load_all_face_encodings_db,
    save_face_encodings_db,
    load_face_encodings_db,
    delete_face_encodings_db,
)

MAX_SAMPLES = 5


def load_encodings() -> dict:
    """Load {user_id: [encoding, ...]} from the database."""
    return load_all_face_encodings_db()


def _to_rgb_array(image) -> np.ndarray:
    if isinstance(image, Image.Image):
        return np.array(image.convert("RGB"))
    arr = np.array(image)
    if arr.ndim == 3 and arr.shape[2] == 4:
        return arr[:, :, :3]
    return arr


def encode_image(image) -> tuple:
    """
    Detect exactly one face and return its encoding.
    Returns (encoding, None) on success, (None, error_str) on failure.
    """
    img = _to_rgb_array(image)
    locations = face_recognition.face_locations(img, model="hog")
    if len(locations) == 0:
        return None, "No face detected. Move closer and ensure good lighting."
    if len(locations) > 1:
        return None, f"{len(locations)} faces in frame. Only one person should be visible."
    encoding = face_recognition.face_encodings(img, locations)[0]
    return encoding, None


def save_face_encodings_bulk(user_id: int, encoding_list: list) -> bool:
    """
    Permanently save a list of face encodings for user_id into the database.
    Existing encodings for this user are replaced.
    """
    if not encoding_list:
        return False
    trimmed = encoding_list[-MAX_SAMPLES:]
    save_face_encodings_db(user_id, trimmed)
    return True


def add_face_encoding(user_id: int, encoding: np.ndarray) -> int:
    """
    Append one encoding to the student's existing training set in the database.
    Returns total sample count after adding.
    """
    existing = load_face_encodings_db(user_id)
    existing.append(encoding)
    if len(existing) > MAX_SAMPLES:
        existing = existing[-MAX_SAMPLES:]
    save_face_encodings_db(user_id, existing)
    return len(existing)


def delete_face_encodings(user_id: int) -> bool:
    delete_face_encodings_db(user_id)
    return True


def recognize_faces(image, tolerance: float = 0.55) -> tuple:
    """
    Identify all faces in an image against the DB-stored encodings.
    Returns (results_list, error_str|None).
    Each result: {"user_id": int|None, "location": tuple, "confidence": float}
    """
    img = _to_rgb_array(image)
    encodings = load_encodings()

    if not encodings:
        return [], "No student faces trained yet. Please register students first."

    known_ids: list = []
    known_encodings: list = []
    for uid, enc_list in encodings.items():
        for enc in enc_list:
            known_ids.append(uid)
            known_encodings.append(enc)

    locations = face_recognition.face_locations(img, model="hog")
    face_encodings = face_recognition.face_encodings(img, locations)

    results = []
    for encoding, location in zip(face_encodings, locations):
        distances = face_recognition.face_distance(known_encodings, encoding)
        best_idx = int(np.argmin(distances))
        best_dist = float(distances[best_idx])

        if best_dist <= tolerance:
            uid = known_ids[best_idx]
            confidence = round((1 - best_dist) * 100, 1)
        else:
            uid = None
            confidence = 0.0

        results.append({"user_id": uid, "location": location, "confidence": confidence})

    return results, None


def draw_annotations(image, results: list, user_map: dict = None) -> np.ndarray:
    """Draw bounding boxes and name labels on a copy of image."""
    img = _to_rgb_array(image).copy()

    for r in results:
        top, right, bottom, left = r["location"]
        uid = r["user_id"]
        conf = r["confidence"]

        if uid and user_map and uid in user_map:
            label = f"{user_map[uid]} ({conf}%)"
            color = (34, 197, 94)
        elif uid:
            label = f"ID:{uid} ({conf}%)"
            color = (34, 197, 94)
        else:
            label = "Unknown"
            color = (239, 68, 68)

        cv2.rectangle(img, (left, top), (right, bottom), color, 2)
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(img, (left, bottom), (left + lw + 8, bottom + 26), color, cv2.FILLED)
        cv2.putText(img, label, (left + 4, bottom + 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    return img
