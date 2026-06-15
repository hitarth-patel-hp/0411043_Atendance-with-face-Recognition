import os
from werkzeug.utils import secure_filename
import base64
import cv2
import numpy as np

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder='faces'):
    """Save uploaded file to folder"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        file.save(filepath)
        return filepath
    return None

def base64_to_cv2(base64_image):
    """Convert base64 image to OpenCV format"""
    try:
        img_data = base64.b64decode(base64_image)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"Error converting base64: {e}")
        return None

def cv2_to_base64(image):
    """Convert OpenCV image to base64"""
    try:
        _, buffer = cv2.imencode('.jpg', image)
        base64_image = base64.b64encode(buffer).decode()
        return base64_image
    except Exception as e:
        print(f"Error converting to base64: {e}")
        return None