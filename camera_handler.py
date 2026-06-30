# modules/camera_handler.py
# OpenCV se webcam feed PyQt5 mein dikhata hai
# UPDATED: Mobile/phone detection (YOLOv8n) + 3-strike cheating system added

import cv2
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from config import CAMERA_INDEX
from modules.face_detector import FaceDetector

# ──────────────────────────────────────────────────────────────────────
# NEW: YOLO model lazy-load karo (sirf ek baar, jab pehli baar zaroorat ho)
# Agar ultralytics install nahi hai, toh phone detection silently
# disable ho jayega — face detection phir bhi chalti rahegi.
# ──────────────────────────────────────────────────────────────────────
_YOLO_MODEL = None
_YOLO_AVAILABLE = True


def _get_yolo_model():
    global _YOLO_MODEL, _YOLO_AVAILABLE
    if _YOLO_MODEL is None and _YOLO_AVAILABLE:
        try:
            from ultralytics import YOLO
            _YOLO_MODEL = YOLO("yolov8n.pt")   # pehli baar download hoga
            print("[Camera] YOLOv8n model load ho gaya — phone detection ON")
        except Exception as e:
            _YOLO_AVAILABLE = False
            print(f"[Camera] YOLO load nahi hua, phone detection OFF: {e}")
    return _YOLO_MODEL


# COCO dataset mein "cell phone" class id = 67
PHONE_CLASS_ID = 67
PHONE_CONFIDENCE_THRESHOLD = 0.45


class CameraThread(QThread):
    """
    Background thread jo continuously webcam frames capture karta hai
    aur PyQt5 signal ke through UI ko bhejta hai.

    UPDATED:
    - Face detection (jaisa pehle tha)
    - NEW: Phone/mobile detection (YOLOv8n)
    - NEW: 3-strike system — har violation (no_face / multiple_faces /
      phone_detected) 3 baar tak warning degi, 4th baar interview
      auto-cancel ho jayegi (interview_cancelled signal emit hoga)
    """

    frame_ready  = pyqtSignal(QImage)          # Existing — Qt frame for display
    camera_error = pyqtSignal(str)             # Existing — error message
    face_status  = pyqtSignal(int, str, list)  # Existing — (face_count, status, faces)

    # NEW signals
    cheat_warning       = pyqtSignal(str, int)   # (message, strike_count)
    interview_cancelled = pyqtSignal(str)        # (reason)

    MAX_STRIKES = 3                   # 3 tak tolerate, 4th pe cancel
    VIOLATION_CONFIRM_CHECKS = 4      # violation ko itni baar consecutively dekhne ke baad hi "strike" maano (false positive avoid karne ke liye)
    VIOLATION_COOLDOWN_SECONDS = 4    # ek strike count hone ke baad itne second tak dobara strike nahi lagega (same violation ko baar baar count na kare)

    def __init__(self, camera_index=CAMERA_INDEX):
        super().__init__()
        self.camera_index  = camera_index
        self.is_running    = False
        self.cap           = None
        self.mirror        = True   # Selfie mode

        # Face detector instance (lives in this thread)
        self.face_detector = FaceDetector()

        # Face/phone detection har frame pe nahi, har 3rd frame pe (performance)
        self._frame_count  = 0
        self._last_status  = "ok"
        self._last_faces   = []
        self._last_phone_detected = False

        # ── NEW: Cheating strike tracking ──────────────────────────
        self.strike_count       = 0
        self._cancelled         = False
        self._consecutive_violation_checks = 0
        self._current_violation_type       = None   # "no_face" | "multiple_faces" | "phone_detected"
        self._last_strike_time  = 0
        self._cheat_log         = []   # [{type, timestamp, strike_no}, ...]

    # ------------------------------------------------------------------

    def run(self):
        """Thread start hone par ye run hota hai"""
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            self.camera_error.emit(f"Camera {self.camera_index} open nahi hua!")
            return

        # Camera settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS,          30)

        # Phone detection model preload karo (taaki interview ke beech
        # mein pehli baar lazy-load se lag/freeze na ho)
        _get_yolo_model()

        self.is_running = True

        while self.is_running:
            ret, frame = self.cap.read()

            if not ret:
                self.camera_error.emit("Camera frame read nahi hua!")
                break

            # Mirror flip (selfie mode)
            if self.mirror:
                frame = cv2.flip(frame, 1)

            # ── Face + Phone detection (har 3rd frame) ────────────────
            self._frame_count += 1
            if self._frame_count % 3 == 0:
                face_count, faces, face_status_val = self.face_detector.check_frame(frame)
                self._last_status = face_status_val
                self._last_faces  = faces
                self.face_status.emit(face_count, face_status_val, faces)

                phone_detected = self._detect_phone(frame)
                self._last_phone_detected = phone_detected

                # ── NEW: Combined violation evaluate karo ──────────
                self._evaluate_violation(face_status_val, phone_detected)
            # ─────────────────────────────────────────────────────────

            if self._cancelled:
                break

            # ── Face boxes + status draw karo frame pe ────────────────
            display_frame = self.face_detector.draw_faces(
                frame.copy(), self._last_faces, self._last_status
            )

            # NEW: Phone detect hua toh frame pe bhi dikhao
            if self._last_phone_detected:
                cv2.putText(display_frame, "PHONE DETECTED!", (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            # ─────────────────────────────────────────────────────────

            # Recording indicator (red dot) — existing
            cv2.circle(display_frame, (20, 20), 8, (0, 0, 255), -1)
            cv2.putText(display_frame, "REC", (32, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # BGR → RGB → QImage
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h, w, ch  = rgb_frame.shape
            qt_image  = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)

            self.frame_ready.emit(qt_image)
            self.msleep(33)   # ~30 FPS

        # Cleanup
        if self.cap:
            self.cap.release()

    # ------------------------------------------------------------------
    # NEW: Phone detection
    # ------------------------------------------------------------------

    def _detect_phone(self, frame) -> bool:
        """Frame mein cell phone hai ya nahi, YOLOv8n se check karo."""
        model = _get_yolo_model()
        if model is None:
            return False
        try:
            results = model.predict(
                frame, classes=[PHONE_CLASS_ID],
                conf=PHONE_CONFIDENCE_THRESHOLD, verbose=False
            )
            for r in results:
                if r.boxes is not None and len(r.boxes) > 0:
                    return True
            return False
        except Exception as e:
            print(f"[Camera] Phone detection error: {e}")
            return False

    # ------------------------------------------------------------------
    # NEW: Violation / strike logic
    # ------------------------------------------------------------------

    def _evaluate_violation(self, face_status_val: str, phone_detected: bool):
        """
        Har detection-check pe yeh decide karta hai ki abhi koi
        cheating violation chal rahi hai ya nahi, aur agar same
        violation lagatar VIOLATION_CONFIRM_CHECKS baar dikhe,
        toh ek "strike" count karta hai (cooldown ke saath, taaki
        ek hi violation baar baar strike na de).
        """
        if self._cancelled:
            return

        # Priority: phone > multiple_faces > no_face > ok
        if phone_detected:
            violation_type = "phone_detected"
        elif face_status_val == "multiple_faces":
            violation_type = "multiple_faces"
        elif face_status_val == "no_face":
            violation_type = "no_face"
        else:
            violation_type = None

        if violation_type is None:
            self._consecutive_violation_checks = 0
            self._current_violation_type = None
            return

        if violation_type == self._current_violation_type:
            self._consecutive_violation_checks += 1
        else:
            self._current_violation_type = violation_type
            self._consecutive_violation_checks = 1

        # Confirm hone ke baad hi strike do
        if self._consecutive_violation_checks < self.VIOLATION_CONFIRM_CHECKS:
            return

        now = time.time()
        if now - self._last_strike_time < self.VIOLATION_COOLDOWN_SECONDS:
            return   # cooldown active, dobara strike mat do

        self._last_strike_time = now
        self._consecutive_violation_checks = 0   # reset, agla strike fresh se confirm hoga
        self.strike_count += 1

        messages = {
            "phone_detected":  "📱 Mobile phone detected! Yeh interview mein allowed nahi hai.",
            "multiple_faces":  "🚨 Multiple faces detected! Sirf candidate allowed hai.",
            "no_face":         "⚠️ Face frame mein nahi hai! Camera ke saamne raho.",
        }
        msg = messages.get(violation_type, "⚠️ Suspicious activity detected!")

        self._cheat_log.append({
            "type": violation_type,
            "timestamp": now,
            "strike_no": self.strike_count,
        })

        if self.strike_count > self.MAX_STRIKES:
            reason = (
                f"Interview cancelled: {self.MAX_STRIKES} warnings ke baad bhi "
                f"cheating activity ({violation_type.replace('_', ' ')}) continue hui."
            )
            self._cancelled = True
            self.interview_cancelled.emit(reason)
            self.is_running = False
        else:
            self.cheat_warning.emit(
                f"{msg}  (Warning {self.strike_count}/{self.MAX_STRIKES})",
                self.strike_count
            )

    def stop(self):
        """Camera band karo"""
        self.is_running = False
        self.wait(2000)
        if self.cap and self.cap.isOpened():
            self.cap.release()

    # Question index update karo (InterviewScreen se call hoga)
    def set_question_index(self, index: int):
        self.face_detector.set_question_index(index)

    # End of interview pe cheating report lo
    def get_cheat_report(self) -> dict:
        report = self.face_detector.get_report()
        # NEW: phone detection data bhi merge karo
        phone_incidents = [e for e in self._cheat_log if e["type"] == "phone_detected"]
        report["phone_incidents"] = len(phone_incidents)
        report["total_strikes"]   = self.strike_count
        report["cheat_log"]       = self._cheat_log
        # total_incidents ko update karo taaki phone bhi count ho
        report["total_incidents"] = report.get("total_incidents", 0) + len(phone_incidents)
        return report

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