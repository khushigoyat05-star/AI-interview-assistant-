# main.py
# AI Interview Assistant - Main Entry Point
# Screens manage karta hai: Home → Interview → Report

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont


class AIInterviewApp(QMainWindow):
    """
    Main Application Window
    QStackedWidget se screens switch hoti hain:
        - Index 0: Main Window (Resume Upload)
        - Index 1: Interview Screen (Camera + Q&A)
        - Index 2: Report Screen (Results + PDF)
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 AI Interview Assistant")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 800)
        
        # Center window on screen
        self.center_window()
        
        # Main stacked widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Home screen load karo
        self.show_home_screen()
    
    def center_window(self):
        """Window ko screen ke center mein rakho"""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def show_home_screen(self):
        """Home screen dikhao"""
        from ui.main_window import MainWindow
        
        # Purani screens remove karo
        while self.stack.count() > 0:
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        
        home = MainWindow()
        home.start_interview_signal.connect(self.show_interview_screen)
        self.stack.addWidget(home)
        self.stack.setCurrentIndex(0)
    
    def show_interview_screen(self, candidate_info):
        """Interview screen dikhao"""
        from ui.interview_screen import InterviewScreen
        
        if not candidate_info.get("_questions"):
            QMessageBox.warning(self, "Error", "No any question is generated! first analyse the resume.")
            return
        
        interview = InterviewScreen(candidate_info)
        interview.interview_complete.connect(self.show_report_screen)
        
        self.stack.addWidget(interview)
        self.stack.setCurrentWidget(interview)
    
    def show_report_screen(self, candidate_info, qa_pairs):
        """Report screen dikhao"""
        from ui.report_screen import ReportScreen
        
        if not qa_pairs:
            QMessageBox.warning(self, "Error", "No any answer is recorded!")
            return
        
        report = ReportScreen(candidate_info, qa_pairs)
        report.restart_signal.connect(self.show_home_screen)
        
        self.stack.addWidget(report)
        self.stack.setCurrentWidget(report)
    
    def closeEvent(self, event):
        """App band hone par cleanup"""
        reply = QMessageBox.question(
            self,
            "Close?",
            "Do you wanna to close ai assistant?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    """Application start karo"""
    
    # High DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("AI Interview Assistant")
    app.setApplicationVersion("1.0.0")
    
    # Global font set karo
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # App style
    app.setStyle("Fusion")
    
    # Main window
    window = AIInterviewApp()
    window.show()
    
    print("=" * 50)
    print("🎯 AI Interview Assistant Started!")
    print("=" * 50)
    print(f"✅ PyQt5 UI loaded")
    print(f"✅ Groq API ready")
    print(f"✅ Whisper STT ready")
    print(f"✅ Camera module ready")
    print(f"✅ PDF report generator ready")
    print("=" * 50)
    print("config.py mein apni Groq API Key daalo!")
    print("=" * 50)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
