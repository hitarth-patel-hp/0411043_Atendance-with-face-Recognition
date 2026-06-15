# app/services/face_recognition.py
import cv2
import dlib
import numpy as np
from pathlib import Path
import pickle

class FaceRecognitionService:
    def __init__(self):
        # Load dlib's face detector and shape predictor
        self.detector = dlib.get_frontal_face_detector()
        
        # Download shape predictor from: 
        # http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
        self.sp = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
        self.facerec = dlib.face_recognition_model_v1("models/mmod_human_face_detector.dat")
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.tolerance = 0.6  # Tolerance for face matching

    def get_face_encoding(self, image_path):
        """Extract face encoding from an image"""
        img = cv2.imread(image_path)
        dets = self.detector(img, 1)
        
        if len(dets) == 0:
            return None
        
        # Get encoding for first detected face
        face = dets[0]
        shape = self.sp(img, face)
        face_descriptor = self.facerec.compute_face_descriptor(img, shape)
        return np.array(face_descriptor)

    def register_user(self, user_id, image_path):
        """Register a user's face"""
        encoding = self.get_face_encoding(image_path)
        if encoding is not None:
            self.known_face_encodings.append(encoding)
            self.known_face_names.append(user_id)
            return True
        return False

    def recognize_face(self, image_path):
        """Recognize a face and return user_id"""
        encoding = self.get_face_encoding(image_path)
        if encoding is None:
            return None, 0

        # Compare with known faces
        distances = np.linalg.norm(
            np.array(self.known_face_encodings) - encoding, 
            axis=1
        )
        
        min_distance_index = np.argmin(distances)
        min_distance = distances[min_distance_index]

        if min_distance < self.tolerance:
            return self.known_face_names[min_distance_index], min_distance
        
        return None, min_distance

    def recognize_from_webcam(self):
        """Real-time face recognition from webcam"""
        cap = cv2.VideoCapture(0)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            dets = self.detector(frame, 1)
            
            for face in dets:
                shape = self.sp(frame, face)
                encoding = self.facerec.compute_face_descriptor(frame, shape)
                
                user_id, confidence = self.recognize_face_from_encoding(encoding)
                
                # Draw rectangle and name
                left = face.left()
                top = face.top()
                right = face.right()
                bottom = face.bottom()
                
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                label = user_id if user_id else "Unknown"
                cv2.putText(frame, label, (left, top-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imshow('Face Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()