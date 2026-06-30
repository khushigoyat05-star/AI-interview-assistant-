# ui/cancelled_screen.py
# Jab cheating ki vajah se interview force-cancel ho jaaye, yeh screen dikhti hai

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class CancelledScreen(QWidget):

    restart_signal = pyqtSignal()

    def __init__(self, reason: str, cheat_report: dict = None):
        super().__init__()
        self.reason = reason
        self.cheat_report = cheat_report or {}
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #1a1a2e; color: white;
                      font-family: 'Segoe UI', Arial, sans-serif; }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(60, 60, 60, 60)

        emoji = QLabel("🚫")
        emoji.setFont(QFont("Segoe UI", 56))
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(emoji)

        title = QLabel("Interview Cancelled")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e94560; background: transparent; border: none;")
        layout.addWidget(title)

        reason_frame = QFrame()
        reason_frame.setStyleSheet("""
            QFrame { background: #2d1b24; border-radius: 12px;
                     border: 1px solid #e94560; }
        """)
        reason_layout = QVBoxLayout(reason_frame)
        reason_layout.setContentsMargins(20, 15, 20, 15)

        reason_label = QLabel(self.reason)
        reason_label.setWordWrap(True)
        reason_label.setAlignment(Qt.AlignCenter)
        reason_label.setStyleSheet(
            "color: #ffb3b3; font-size: 13px; background: transparent; border: none;")
        reason_layout.addWidget(reason_label)
        layout.addWidget(reason_frame)

        total_strikes = self.cheat_report.get("total_strikes", 0)
        if total_strikes:
            strikes_label = QLabel(f"Total warnings before cancellation: {total_strikes}")
            strikes_label.setAlignment(Qt.AlignCenter)
            strikes_label.setStyleSheet(
                "color: #b2bec3; font-size: 11px; background: transparent; border: none;")
            layout.addWidget(strikes_label)

        restart_btn = QPushButton("🔄 Start New Interview")
        restart_btn.setFixedHeight(45)
        restart_btn.setFixedWidth(220)
        restart_btn.setCursor(Qt.PointingHandCursor)
        restart_btn.setStyleSheet("""
            QPushButton { background: #4caf50; color: white; border: none;
                          border-radius: 22px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background: #66bb6a; }
        """)
        restart_btn.clicked.connect(self.restart_signal.emit)
        layout.addWidget(restart_btn, alignment=Qt.AlignCenter)