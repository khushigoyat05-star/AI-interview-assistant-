# modules/camera_handler.py
# OpenCV se webcam feed PyQt5 mein dikhata hai

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from config import CAMERA_INDEX


class CameraThread(QThread):
    """
    Background thread jo continuously webcam frames capture karta hai
    aur PyQt5 signal ke through UI ko bhejta hai
    """
    
    frame_ready = pyqtSignal(QImage)   # Naya frame aaya signal
    camera_error = pyqtSignal(str)      # Camera error signal
    
    def __init__(self, camera_index=CAMERA_INDEX):
        super().__init__()
        self.camera_index = camera_index
        self.is_running = False
        self.cap = None
        self.mirror = True  # Selfie mode (mirror)
    
    def run(self):
        """Thread start hone par ye run hota hai"""
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            self.camera_error.emit(f"Camera {self.camera_index} open nahi hua!")
            return
        
        # Camera settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_running = True
        
        while self.is_running:
            ret, frame = self.cap.read()
            
            if not ret:
                self.camera_error.emit("Camera frame read nahi hua!")
                break
            
            # Mirror flip karo (selfie mode)
            if self.mirror:
                frame = cv2.flip(frame, 1)
            
            # Recording indicator dikhao (red dot)
            if self.is_running:
                cv2.circle(frame, (20, 20), 8, (0, 0, 255), -1)
                cv2.putText(frame, "REC", (32, 26), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # OpenCV BGR → RGB convert karo
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # QImage banao
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Signal emit karo
            self.frame_ready.emit(qt_image)
            
            # ~30 FPS ke liye wait karo
            self.msleep(33)
        
        # Cleanup
        if self.cap:
            self.cap.release()
    
    def stop(self):
        """Camera band karo"""
        self.is_running = False
        self.wait(2000)  # Max 2 seconds wait
        if self.cap and self.cap.isOpened():
            self.cap.release()
    
    def take_snapshot(self) -> np.ndarray:
        """Ek frame capture karo (future use ke liye)"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                if self.mirror:
                    frame = cv2.flip(frame, 1)
                return frame
        return None


def check_camera_available(camera_index=CAMERA_INDEX) -> bool:
    """Check karo camera available hai ya nahi"""
    cap = cv2.VideoCapture(camera_index)
    available = cap.isOpened()
    cap.release()
    return available
