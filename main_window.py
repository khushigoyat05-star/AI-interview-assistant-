# ui/main_window.py
# Main home screen - Resume upload aur interview start

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QFileDialog, QProgressBar, QFrame,
                              QScrollArea, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor, QPainter, QLinearGradient


class ResumeAnalysisThread(QThread):
    """Background mein resume parse karne ke liye thread"""
    progress = pyqtSignal(int, str)     # (percentage, message)
    finished = pyqtSignal(dict)          # candidate_info dict
    error = pyqtSignal(str)             # error message
    
    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path
    
    def run(self):
        try:
            from modules.resume_parser import parse_resume
            from modules.question_gen import generate_interview_questions
            
            self.progress.emit(20, "Text is extracting from the pdf...")
            candidate_info = parse_resume(self.pdf_path)
            
            self.progress.emit(60, "Skills are identifying...")
            self.msleep(500)
            
            self.progress.emit(80, "Interview questions are generating...")
            questions = generate_interview_questions(candidate_info)
            candidate_info["_questions"] = questions
            
            self.progress.emit(100, "Ready!")
            self.finished.emit(candidate_info)
            
        except Exception as e:
            self.error.emit(str(e))


class SkillChip(QLabel):
    """Individual skill chip widget"""
    def __init__(self, text, color="#0f3460"):
        super().__init__(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)


class MainWindow(QWidget):
    
    start_interview_signal = pyqtSignal(dict)  # candidate_info bhejo interview screen ko
    
    def __init__(self):
        super().__init__()
        self.candidate_info = None
        self.pdf_path = None
        self.analysis_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #16213e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #0f3460;
                border-radius: 4px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #1a1a2e;")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(40, 30, 40, 30)
        self.content_layout.setSpacing(20)
        
        # Upload section
        upload_section = self.create_upload_section()
        self.content_layout.addWidget(upload_section)
        
        # Progress section (initially hidden)
        self.progress_frame = self.create_progress_section()
        self.progress_frame.setVisible(False)
        self.content_layout.addWidget(self.progress_frame)
        
        # Results section (initially hidden)
        self.results_frame = QFrame()
        self.results_frame.setVisible(False)
        self.results_layout = QVBoxLayout(self.results_frame)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addWidget(self.results_frame)
        
        self.content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def create_header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border-bottom: 2px solid #e94560;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 0, 40, 0)
        
        # Logo + Title
        title_layout = QVBoxLayout()
        title_label = QLabel("🎯 AI Interview Assistant")
        title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title_label.setStyleSheet("color: white; border: none; background: transparent;")
        
        subtitle_label = QLabel("Smart • Accurate • Insightful")
        subtitle_label.setFont(QFont("Segoe UI", 10))
        subtitle_label.setStyleSheet("color: #b2bec3; border: none; background: transparent;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Status badge
        self.status_badge = QLabel("● Ready")
        self.status_badge.setStyleSheet("""
            color: #4caf50;
            font-size: 12px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.status_badge)
        
        return header
    
    def create_upload_section(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #16213e;
                border-radius: 16px;
                border: 2px dashed #0f3460;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon
        icon_label = QLabel("📄")
        icon_label.setFont(QFont("Segoe UI", 48))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_label)
        
        # Title
        title = QLabel("Upload Your Resume")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Upload your resume in PDF format\n System will analyse your resume using ai and generate interview questions")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #b2bec3; background: transparent; border: none; line-height: 1.5;")
        # layout.addWidget(subtitle)
        
        # File info label
        self.file_label = QLabel("No any file selected")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet("""
            color: #636e72;
            font-size: 11px;
            background: #0f3460;
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
        """)
        layout.addWidget(self.file_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.setSpacing(15)
        
        self.upload_btn = QPushButton("📂 Choose Resume")
        self.upload_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.upload_btn.setFixedSize(220, 48)
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: #0f3460;
                color: white;
                border: none;
                border-radius: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1e5799;
            }
            QPushButton:pressed {
                background: #0a2444;
            }
        """)
        self.upload_btn.clicked.connect(self.select_pdf)
        btn_layout.addWidget(self.upload_btn)
        
        self.analyze_btn = QPushButton("🔍  Analyse ")
        self.analyze_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.analyze_btn.setFixedSize(180, 48)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: #e94560;
                color: white;
                border: none;
                border-radius: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff6b81;
            }
            QPushButton:disabled {
                background: #4a4a6a;
                color: #888;
            }
        """)
        self.analyze_btn.clicked.connect(self.start_analysis)
        btn_layout.addWidget(self.analyze_btn)
        
        layout.addLayout(btn_layout)
        
        # Features
        features_layout = QHBoxLayout()
        features_layout.setAlignment(Qt.AlignCenter)
        features_layout.setSpacing(20)
        
        features = ["✅ Skills Extract", "✅ Custom Questions", "✅ AI Evaluation", "✅ PDF Report"]
        for feat in features:
            feat_label = QLabel(feat)
            feat_label.setStyleSheet("color: #4caf50; font-size: 11px; background: transparent; border: none;")
            features_layout.addWidget(feat_label)
        
        layout.addLayout(features_layout)
        
        return frame
    
    def create_progress_section(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #16213e;
                border-radius: 12px;
                border: 1px solid #0f3460;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(12)
        
        self.progress_title = QLabel("⏳ Resume is Analysing...")
        self.progress_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.progress_title.setStyleSheet("color: white; background: transparent; border: none;")
        layout.addWidget(self.progress_title)
        
        self.progress_msg = QLabel("PDF is loading...")
        self.progress_msg.setStyleSheet("color: #b2bec3; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(self.progress_msg)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #0f3460;
                border-radius: 5px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #0f3460);
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        return frame
    
    def select_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Resume Select Karo",
            "",
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            self.pdf_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.setText(f"📄 {filename}")
            self.file_label.setStyleSheet("""
                color: #4caf50;
                font-size: 11px;
                background: #16213e;
                padding: 8px 16px;
                border-radius: 8px;
                border: 1px solid #4caf50;
            """)
            self.analyze_btn.setEnabled(True)
            self.status_badge.setText("● Resume Ready")
            self.status_badge.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold; background: transparent; border: none;")
    
    def start_analysis(self):
        if not self.pdf_path:
            return
        
        # UI update
        self.analyze_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)
        self.progress_frame.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Results clear karo agar pehle se hai
        self.results_frame.setVisible(False)
        for i in reversed(range(self.results_layout.count())):
            self.results_layout.itemAt(i).widget().deleteLater()
        
        # Background thread mein analyse karo
        self.analysis_thread = ResumeAnalysisThread(self.pdf_path)
        self.analysis_thread.progress.connect(self.update_progress)
        self.analysis_thread.finished.connect(self.analysis_done)
        self.analysis_thread.error.connect(self.analysis_error)
        self.analysis_thread.start()
        
        self.status_badge.setText("● Analysing...")
        self.status_badge.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold; background: transparent; border: none;")
    
    def update_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.progress_msg.setText(message)
    
    def analysis_done(self, candidate_info):
        self.candidate_info = candidate_info
        self.progress_frame.setVisible(False)
        self.upload_btn.setEnabled(True)
        
        self.status_badge.setText("● Ready to Interview")
        self.status_badge.setStyleSheet("color: #4caf50; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        
        self.show_candidate_results(candidate_info)
    
    def analysis_error(self, error_msg):
        self.progress_frame.setVisible(False)
        self.upload_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.status_badge.setText("● Error")
        self.status_badge.setStyleSheet("color: #e94560; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        
        error_label = QLabel(f"❌ Error: {error_msg}")
        error_label.setStyleSheet("color: #e94560; padding: 10px; background: #2d1b24; border-radius: 8px;")
        error_label.setWordWrap(True)
        self.content_layout.insertWidget(self.content_layout.count() - 1, error_label)
    
    def show_candidate_results(self, info):
        """Candidate ki extracted info dikhao"""
        self.results_frame.setVisible(True)
        
        # Clear existing
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Header
        header = QLabel(f"✅ Resume is Analysed - {info.get('name', 'Candidate')}")
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setStyleSheet("color: #4caf50; background: transparent; border: none;")
        self.results_layout.addWidget(header)
        
        # Info grid
        info_frame = QFrame()
        info_frame.setStyleSheet("background: #16213e; border-radius: 12px; border: 1px solid #0f3460;")
        info_grid = QGridLayout(info_frame)
        info_grid.setContentsMargins(20, 15, 20, 15)
        
        info_items = [
            ("👤 Naam", info.get("name", "N/A")),
            ("💼 Role", info.get("current_role", "N/A")),
            ("⏳ Experience", info.get("total_experience", "N/A")),
            ("🎓 Education", info.get("education", "N/A")),
        ]
        
        for idx, (label, value) in enumerate(info_items):
            row, col = divmod(idx, 2)
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #b2bec3; font-size: 11px; background: transparent; border: none;")
            
            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("color: white; font-weight: bold; font-size: 12px; background: transparent; border: none;")
            value_widget.setWordWrap(True)
            
            info_grid.addWidget(label_widget, row * 2, col)
            info_grid.addWidget(value_widget, row * 2 + 1, col)
        
        self.results_layout.addWidget(info_frame)
        
        # Skills
        tech_skills = info.get("technical_skills", [])
        if tech_skills:
            skills_label = QLabel("💡 Extracted Skills:")
            skills_label.setStyleSheet("color: #b2bec3; font-size: 12px; background: transparent; border: none;")
            self.results_layout.addWidget(skills_label)
            
            skills_frame = QFrame()
            skills_frame.setStyleSheet("background: #16213e; border-radius: 10px; border: 1px solid #0f3460; padding: 10px;")
            skills_flow = QHBoxLayout(skills_frame)
            skills_flow.setFlexibleDirection = True
            
            for skill in tech_skills[:12]:
                chip = SkillChip(skill)
                skills_flow.addWidget(chip)
            skills_flow.addStretch()
            
            self.results_layout.addWidget(skills_frame)
        
        # Questions count
        questions = info.get("_questions", [])
        q_label = QLabel(f"❓ {len(questions)} Interview Questions Ready")
        q_label.setStyleSheet("color: #4caf50; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        self.results_layout.addWidget(q_label)
        
        # Start Interview Button
        start_btn = QPushButton("🚀 Start the Interview")
        start_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        start_btn.setFixedHeight(55)
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #0f3460);
                color: white;
                border: none;
                border-radius: 27px;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b81, stop:1 #1e5799);
            }
        """)
        start_btn.clicked.connect(self.start_interview)
        self.results_layout.addWidget(start_btn)
    
    def start_interview(self):
        if self.candidate_info:
            self.start_interview_signal.emit(self.candidate_info)
