# ui/interview_screen.py
# Interview screen - Camera feed, questions aur audio recording

import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QFrame, QProgressBar, QTextEdit, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage


class TranscribeEvaluateThread(QThread):
    """Transcribe the Audio and evaluate the answer"""
    done = pyqtSignal(str, dict)  # (transcribed_text, evaluation)
    error = pyqtSignal(str)
    
    def __init__(self, audio_path, question, candidate_info):
        super().__init__()
        self.audio_path = audio_path
        self.question = question
        self.candidate_info = candidate_info
    
    def run(self):
        try:
            # FIX: speech_handler → audio_recorder (sahi module naam)
            from modules.audio_recorder import transcribe_audio
            from modules.evaluator import evaluate_answer
            
            # Transcribe
            text = transcribe_audio(self.audio_path)
            
            # Evaluate
            evaluation = evaluate_answer(self.question, text, self.candidate_info)
            
            self.done.emit(text, evaluation)
        except Exception as e:
            self.error.emit(str(e))


class InterviewScreen(QWidget):
    
    interview_complete = pyqtSignal(dict, list)  # (candidate_info, qa_pairs)
    
    def __init__(self, candidate_info):
        super().__init__()
        self.candidate_info = candidate_info
        self.questions = candidate_info.get("_questions", [])
        self.current_q_index = 0
        self.qa_pairs = []
        self.recorder = None
        self.is_recording = False
        self.camera_thread = None
        self.answer_timer = None
        self.elapsed_timer = None
        self.elapsed_seconds = 0
        self.answer_saved = False  # FIX: duplicate save rokne ke liye
        self.setup_ui()
        self.start_camera()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ===== LEFT PANEL: Camera =====
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 3)
        
        # ===== RIGHT PANEL: Questions & Controls =====
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
    
    def create_left_panel(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #16213e;
                border-radius: 16px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        cam_header = QHBoxLayout()
        cam_title = QLabel("📹 Live Camera Feed")
        cam_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        cam_title.setStyleSheet("background: transparent; border: none;")
        
        self.rec_indicator = QLabel("● LIVE")
        self.rec_indicator.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        
        cam_header.addWidget(cam_title)
        cam_header.addStretch()
        cam_header.addWidget(self.rec_indicator)
        layout.addLayout(cam_header)
        
        # Camera feed
        self.camera_label = QLabel()
        self.camera_label.setFixedHeight(350)
        self.camera_label.setStyleSheet("""
            QLabel {
                background: #0f3460;
                border-radius: 12px;
                border: 2px solid #0f3460;
            }
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setText("📷\nCamera loading...")
        layout.addWidget(self.camera_label)
        
        # Candidate info
        cand_name = self.candidate_info.get("name", "Candidate")
        cand_role = self.candidate_info.get("current_role", "")
        
        info_label = QLabel(f"👤 {cand_name}  |  💼 {cand_role}")
        info_label.setStyleSheet("color: #b2bec3; font-size: 11px; background: transparent; border: none;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Recording status
        self.recording_status = QLabel("🎤 Press the button for recording")
        self.recording_status.setAlignment(Qt.AlignCenter)
        self.recording_status.setStyleSheet("""
            color: #b2bec3;
            font-size: 11px;
            background: #0f3460;
            padding: 8px;
            border-radius: 8px;
            border: none;
        """)
        layout.addWidget(self.recording_status)
        
        # Timer
        self.timer_label = QLabel("⏱ 0:00")
        self.timer_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("color: white; background: transparent; border: none;")
        layout.addWidget(self.timer_label)
        
        return frame
    
    def create_right_panel(self):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: transparent; }")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Progress header
        progress_frame = QFrame()
        progress_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(15, 12, 15, 12)
        
        progress_header = QHBoxLayout()
        self.q_counter = QLabel(f"Question 1 of {len(self.questions)}")
        self.q_counter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.q_counter.setStyleSheet("background: transparent; border: none;")
        
        self.category_badge = QLabel("Technical")
        self.category_badge.setStyleSheet("""
            background: #0f3460;
            color: white;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 10px;
            border: none;
        """)
        
        progress_header.addWidget(self.q_counter)
        progress_header.addStretch()
        progress_header.addWidget(self.category_badge)
        progress_layout.addLayout(progress_header)
        
        self.q_progress = QProgressBar()
        self.q_progress.setFixedHeight(6)
        self.q_progress.setMaximum(len(self.questions))
        self.q_progress.setValue(0)
        self.q_progress.setStyleSheet("""
            QProgressBar {
                background: #0f3460;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: #e94560;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.q_progress)
        layout.addWidget(progress_frame)
        
        # Question display
        q_frame = QFrame()
        q_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; border: 2px solid #0f3460; }")
        q_layout = QVBoxLayout(q_frame)
        q_layout.setContentsMargins(20, 20, 20, 20)
        
        q_label_title = QLabel("❓ Question:")
        q_label_title.setStyleSheet("color: #b2bec3; font-size: 11px; background: transparent; border: none;")
        q_layout.addWidget(q_label_title)
        
        self.question_label = QLabel()
        self.question_label.setFont(QFont("Segoe UI", 13))
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("""
            color: white;
            background: transparent;
            border: none;
            line-height: 1.5;
        """)
        self.question_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        q_layout.addWidget(self.question_label)
        
        # Skill tested badge
        self.skill_label = QLabel()
        self.skill_label.setStyleSheet("color: #4caf50; font-size: 10px; background: transparent; border: none;")
        q_layout.addWidget(self.skill_label)
        
        layout.addWidget(q_frame)
        
        # Transcription display
        trans_frame = QFrame()
        trans_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; }")
        trans_layout = QVBoxLayout(trans_frame)
        trans_layout.setContentsMargins(15, 12, 15, 12)
        
        trans_title = QLabel("📝 Your Answer (Auto Transcribed):")
        trans_title.setStyleSheet("color: #b2bec3; font-size: 11px; background: transparent; border: none;")
        trans_layout.addWidget(trans_title)
        
        self.transcript_box = QTextEdit()
        self.transcript_box.setReadOnly(True)
        self.transcript_box.setFixedHeight(100)
        self.transcript_box.setPlaceholderText("Your answer will be visible here after recording...")
        self.transcript_box.setStyleSheet("""
            QTextEdit {
                background: #0f3460;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        trans_layout.addWidget(self.transcript_box)
        layout.addWidget(trans_frame)
        
        # Evaluation display
        self.eval_frame = QFrame()
        self.eval_frame.setVisible(False)
        self.eval_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; border: 1px solid #0f3460; }")
        eval_layout = QVBoxLayout(self.eval_frame)
        eval_layout.setContentsMargins(15, 12, 15, 12)
        
        self.eval_label = QLabel()
        self.eval_label.setWordWrap(True)
        self.eval_label.setStyleSheet("color: white; font-size: 11px; background: transparent; border: none; line-height: 1.4;")
        eval_layout.addWidget(self.eval_label)
        layout.addWidget(self.eval_frame)
        
        # Control buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet("QFrame { background: transparent; }")
        btn_layout = QVBoxLayout(btn_frame)
        btn_layout.setSpacing(10)
        
        # Record button
        self.record_btn = QPushButton("🎤  Start Answer Recording")
        self.record_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.record_btn.setFixedHeight(50)
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 25px;
                font-weight: bold;
            }
            QPushButton:hover { background: #66bb6a; }
            QPushButton:disabled { background: #4a4a6a; color: #888; }
        """)
        self.record_btn.clicked.connect(self.toggle_recording)
        btn_layout.addWidget(self.record_btn)
        
        # Next/Skip buttons row
        nav_layout = QHBoxLayout()
        
        self.skip_btn = QPushButton("⏭  Skip")
        self.skip_btn.setFixedHeight(42)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background: #636e72;
                color: white;
                border: none;
                border-radius: 21px;
                font-size: 12px;
            }
            QPushButton:hover { background: #74b9ff; }
        """)
        self.skip_btn.clicked.connect(self.skip_question)
        nav_layout.addWidget(self.skip_btn)
        
        self.next_btn = QPushButton("▶  Next Question")
        self.next_btn.setFixedHeight(42)
        self.next_btn.setEnabled(False)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: #0f3460;
                color: white;
                border: none;
                border-radius: 21px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #1e5799; }
            QPushButton:disabled { background: #2d2d4a; color: #555; }
        """)
        self.next_btn.clicked.connect(self.next_question)
        nav_layout.addWidget(self.next_btn)
        
        btn_layout.addLayout(nav_layout)
        
        # End interview button
        self.end_btn = QPushButton("🏁 End the Interview")
        self.end_btn.setFixedHeight(42)
        self.end_btn.setCursor(Qt.PointingHandCursor)
        self.end_btn.setStyleSheet("""
            QPushButton {
                background: #e94560;
                color: white;
                border: none;
                border-radius: 21px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #ff6b81; }
        """)
        self.end_btn.clicked.connect(self.end_interview)
        btn_layout.addWidget(self.end_btn)
        
        layout.addWidget(btn_frame)
        layout.addStretch()
        
        # Show first question
        self.show_current_question()
        
        return frame
    
    def start_camera(self):
        from modules.camera_handler import CameraThread
        self.camera_thread = CameraThread()
        self.camera_thread.frame_ready.connect(self.update_camera_frame)
        self.camera_thread.camera_error.connect(self.handle_camera_error)
        self.camera_thread.start()
    
    def update_camera_frame(self, qt_image):
        pixmap = QPixmap.fromImage(qt_image)
        scaled = pixmap.scaled(
            self.camera_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled)
    
    def handle_camera_error(self, error_msg):
        self.camera_label.setText(f"📷 Camera Error:\n{error_msg}")
    
    def show_current_question(self):
        if self.current_q_index < len(self.questions):
            q = self.questions[self.current_q_index]
            self.question_label.setText(q.get("question", ""))
            self.skill_label.setText(f"🎯 Testing: {q.get('skill_tested', '')}  |  Difficulty: {q.get('difficulty', '')}")
            self.category_badge.setText(q.get("category", "General"))
            self.q_counter.setText(f"Question {self.current_q_index + 1} of {len(self.questions)}")
            self.q_progress.setValue(self.current_q_index + 1)
            self.transcript_box.clear()
            self.eval_frame.setVisible(False)
            self.next_btn.setEnabled(False)
            self.record_btn.setEnabled(True)
            self.answer_saved = False  # FIX: nayi question ke liye reset
            
            # Record button green reset
            self.record_btn.setText("🎤  Start Answer Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #66bb6a; }
                QPushButton:disabled { background: #4a4a6a; color: #888; }
            """)
            self.recording_status.setText("🎤 Press the button for recording")
            self.recording_status.setStyleSheet("""
                color: #b2bec3;
                font-size: 11px;
                background: #0f3460;
                padding: 8px;
                border-radius: 8px;
                border: none;
            """)
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        from modules.audio_recorder import AudioRecorder  # FIX: sahi module naam
        
        self.is_recording = True
        self.answer_saved = False  # FIX: reset on new recording
        self.recorder = AudioRecorder()
        self.recorder.start_recording()
        
        # Timer start karo
        self.elapsed_seconds = 0
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_timer)
        self.elapsed_timer.start(1000)
        
        # UI update
        self.record_btn.setText("⏹  Stop Recording ")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: #e94560;
                color: white;
                border: none;
                border-radius: 25px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #ff6b81; }
        """)
        self.recording_status.setText("🔴 Recording is going on please speak")
        self.recording_status.setStyleSheet("""
            color: #e94560;
            font-size: 11px;
            background: #2d1b24;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #e94560;
        """)
        self.rec_indicator.setText("🔴 RECORDING")
        self.skip_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
    
    def stop_recording(self):
        if not self.recorder:
            return
        
        self.is_recording = False
        
        if self.elapsed_timer:
            self.elapsed_timer.stop()
        
        # Audio stop karo
        audio_path = self.recorder.stop_recording()
        self.recorder.cleanup()
        self.recorder = None
        
        # UI update
        self.record_btn.setEnabled(False)
        self.record_btn.setText("⏳  Transcribing...")
        self.recording_status.setText("⏳ Answer is transcribing...")
        self.recording_status.setStyleSheet("""
            color: #ff9800;
            font-size: 11px;
            background: #2d2200;
            padding: 8px;
            border-radius: 8px;
            border: none;
        """)
        self.rec_indicator.setText("● PROCESSING")
        self.rec_indicator.setStyleSheet("color: #ff9800; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        
        # Transcribe + evaluate
        current_q = self.questions[self.current_q_index]
        self.trans_thread = TranscribeEvaluateThread(audio_path, current_q, self.candidate_info)
        self.trans_thread.done.connect(self.transcription_done)
        self.trans_thread.error.connect(self.transcription_error)
        self.trans_thread.start()
    
    def update_timer(self):
        self.elapsed_seconds += 1
        mins = self.elapsed_seconds // 60
        secs = self.elapsed_seconds % 60
        self.timer_label.setText(f"⏱ {mins}:{secs:02d}")
        
        # Auto stop at 2 minutes
        if self.elapsed_seconds >= 120:
            self.stop_recording()
    
    def transcription_done(self, text, evaluation):
        # FIX: duplicate save rokna
        if self.answer_saved:
            return
        self.answer_saved = True

        # Show transcript
        if text:
            self.transcript_box.setText(text)
        else:
            self.transcript_box.setText("(No any audio is detected)")
        
        # Show evaluation
        score = evaluation.get("score", 0)
        rating = evaluation.get("rating", "N/A")
        feedback = evaluation.get("detailed_feedback", "")
        
        score_emoji = "🌟" if score >= 8 else "👍" if score >= 6 else "⚠️" if score >= 4 else "❌"
        
        eval_text = f"{score_emoji} Score: <b>{score}/10</b> - {rating}<br><br>{feedback}"
        self.eval_label.setText(eval_text)
        self.eval_frame.setVisible(True)
        
        # Store QA pair
        current_q = self.questions[self.current_q_index]
        self.qa_pairs.append({
            "question": current_q,
            "answer": text,
            "evaluation": evaluation
        })
        
        # UI reset
        self.record_btn.setEnabled(True)
        self.record_btn.setText("🎤Record Again")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: #636e72;
                color: white;
                border: none;
                border-radius: 25px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #74b9ff; }
        """)
        self.recording_status.setText(f"✅ Answer is evaluated ! Score: {score}/10")
        self.recording_status.setStyleSheet("""
            color: #4caf50;
            font-size: 11px;
            background: #1b2e1b;
            padding: 8px;
            border-radius: 8px;
            border: none;
        """)
        self.rec_indicator.setText("● LIVE")
        self.rec_indicator.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        
        self.next_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.timer_label.setText("⏱ 0:00")
    
    def transcription_error(self, error):
        self.record_btn.setEnabled(True)
        self.record_btn.setText("🎤  Dobara Try Karo")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 25px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #66bb6a; }
        """)
        self.recording_status.setText(f"❌ Error: {error}")
        self.recording_status.setStyleSheet("""
            color: #e94560;
            font-size: 11px;
            background: #2d1b24;
            padding: 8px;
            border-radius: 8px;
            border: none;
        """)
        self.skip_btn.setEnabled(True)
    
    def next_question(self):
        self.current_q_index += 1
        if self.current_q_index >= len(self.questions):
            self.end_interview()
        else:
            self.show_current_question()
    
    def skip_question(self):
        """Skip the Question with empty evaluation"""
        # FIX: recording chal rahi ho to pehle band karo
        if self.is_recording:
            self.is_recording = False
            if self.elapsed_timer:
                self.elapsed_timer.stop()
            if self.recorder:
                self.recorder.stop_recording()
                self.recorder.cleanup()
                self.recorder = None

        current_q = self.questions[self.current_q_index]
        self.qa_pairs.append({
            "question": current_q,
            "answer": "(Skipped)",
            "evaluation": {
                "score": 0,
                "rating": "Skipped",
                "strengths": [],
                "improvements": ["Question skiped"],
                "keywords_matched": [],
                "keywords_missed": current_q.get("expected_keywords", []),
                "detailed_feedback": "Candidate ne yeh question skip kar diya."
            }
        })
        self.current_q_index += 1
        if self.current_q_index >= len(self.questions):
            self.end_interview()
        else:
            self.show_current_question()  # FIX: commented out tha, ab sahi hai
    
    def end_interview(self):
        # Camera band karo
        if self.camera_thread:
            self.camera_thread.stop()
        
        # Report page par jao
        self.interview_complete.emit(self.candidate_info, self.qa_pairs)
    
    def closeEvent(self, event):
        if self.camera_thread:
            self.camera_thread.stop()
        super().closeEvent(event)