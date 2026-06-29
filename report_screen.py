# ui/report_screen.py
# Final report screen - interview results aur PDF generate karna

import os
import subprocess
import platform
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QFrame, QScrollArea, QProgressBar, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


class GenerateReportThread(QThread):
    """Generate report in the Background"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, dict)   # (pdf_path, report_data)
    error = pyqtSignal(str)

    def __init__(self, candidate_info, qa_pairs):
        super().__init__()
        self.candidate_info = candidate_info
        self.qa_pairs = qa_pairs

    def run(self):
        try:
            from modules.evaluator import generate_final_report_data
            from modules.report_gen import generate_pdf_report  # FIX: sahi import

            self.progress.emit("Generating final analysis...")
            report_data = generate_final_report_data(self.candidate_info, self.qa_pairs)

            self.progress.emit("Generating PDF report...")
            pdf_path = generate_pdf_report(report_data)

            self.finished.emit(pdf_path, report_data)
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n\n{traceback.format_exc()}")


class ScoreCircle(QLabel):
    """Circular score display"""
    def __init__(self, score, size=80):
        super().__init__()
        self.score = score
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)

        color = self.get_color(score)
        self.setStyleSheet(f"""
            QLabel {{
                background: {color};
                color: white;
                border-radius: {size//2}px;
                font-size: 22px;
                font-weight: bold;
                border: 3px solid white;
            }}
        """)
        self.setText(f"{score}")

    def get_color(self, score):
        if score >= 8: return "#4caf50"
        elif score >= 6: return "#ff9800"
        elif score >= 4: return "#ff6b35"
        else: return "#f44336"


class ReportScreen(QWidget):

    restart_signal = pyqtSignal()

    def __init__(self, candidate_info, qa_pairs):
        super().__init__()
        self.candidate_info = candidate_info
        self.qa_pairs = qa_pairs
        self.report_data = None
        self.pdf_path = None
        self.setup_ui()
        self.generate_report()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #16213e; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #0f3460; border-radius: 4px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = self.create_header()
        main_layout.addWidget(header)

        self.loading_frame = self.create_loading_frame()
        main_layout.addWidget(self.loading_frame)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_scroll.setVisible(False)

        self.results_widget = QWidget()
        self.results_widget.setStyleSheet("background: #1a1a2e;")
        self.results_main_layout = QVBoxLayout(self.results_widget)
        self.results_main_layout.setContentsMargins(30, 20, 30, 30)
        self.results_main_layout.setSpacing(15)

        self.results_scroll.setWidget(self.results_widget)
        main_layout.addWidget(self.results_scroll)

    def create_header(self):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border-bottom: 2px solid #4caf50;
            }
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("🏆 Interview Report")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(title)
        layout.addStretch()

        self.download_btn = QPushButton("📥 Download PDF")
        self.download_btn.setFixedSize(160, 40)
        self.download_btn.setEnabled(False)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50; color: white; border: none;
                border-radius: 20px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #66bb6a; }
            QPushButton:disabled { background: #4a4a6a; color: #888; }
        """)
        self.download_btn.clicked.connect(self.open_pdf)
        layout.addWidget(self.download_btn)

        restart_btn = QPushButton("🔄 New Interview")
        restart_btn.setFixedSize(150, 40)
        restart_btn.setCursor(Qt.PointingHandCursor)
        restart_btn.setStyleSheet("""
            QPushButton {
                background: #e94560; color: white; border: none;
                border-radius: 20px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #ff6b81; }
        """)
        restart_btn.clicked.connect(self.restart_signal.emit)
        layout.addWidget(restart_btn)

        return header

    def create_loading_frame(self):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: transparent; }")

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        emoji = QLabel("⚙️")
        emoji.setFont(QFont("Segoe UI", 48))
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(emoji)

        self.loading_title = QLabel("Generating Final Report...")
        self.loading_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.loading_title.setAlignment(Qt.AlignCenter)
        self.loading_title.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.loading_title)

        self.loading_msg = QLabel("AI is analysing the complete interview...")
        self.loading_msg.setAlignment(Qt.AlignCenter)
        self.loading_msg.setStyleSheet("color: #b2bec3; background: transparent; border: none;")
        layout.addWidget(self.loading_msg)

        self.loading_bar = QProgressBar()
        self.loading_bar.setFixedWidth(400)
        self.loading_bar.setFixedHeight(8)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setStyleSheet("""
            QProgressBar { background: #16213e; border-radius: 4px; border: none; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #4caf50);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.loading_bar, alignment=Qt.AlignCenter)

        # FIX: Error label add kiya - visible hoga sirf error par
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("""
            color: #e94560;
            background: #2d1b24;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e94560;
            font-size: 12px;
        """)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        return frame

    def generate_report(self):
        self.report_thread = GenerateReportThread(self.candidate_info, self.qa_pairs)
        self.report_thread.progress.connect(lambda msg: self.loading_msg.setText(msg))
        self.report_thread.finished.connect(self.report_generated)
        self.report_thread.error.connect(self.report_error)
        self.report_thread.start()

    def report_generated(self, pdf_path, report_data):
        self.pdf_path = pdf_path
        self.report_data = report_data

        self.loading_frame.setVisible(False)
        self.results_scroll.setVisible(True)
        self.download_btn.setEnabled(True)

        self.show_results(report_data)

    def report_error(self, error):
        # FIX: Loading bar band karo, error clearly dikhao
        self.loading_bar.setRange(0, 1)
        self.loading_bar.setValue(0)
        self.loading_title.setText("❌ Report Generation Failed")
        self.loading_title.setStyleSheet("color: #e94560; background: transparent; border: none;")
        self.loading_msg.setText("Please check the error below and try again.")
        self.error_label.setText(f"Error Details:\n{error}")
        self.error_label.setVisible(True)
        print(f"[Report Error] {error}")

    def show_results(self, report_data):
        summary = report_data["summary"]
        analysis = report_data["final_analysis"]
        candidate = report_data["candidate_info"]
        qa_pairs = report_data["qa_pairs"]

        avg_score = summary["average_score"]
        verdict = analysis.get("overall_verdict", "Consider")

        # ===== SCORE HERO SECTION =====
        hero = QFrame()
        hero.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #16213e, stop:1 #0f3460);
                border-radius: 16px;
            }
        """)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(30, 25, 30, 25)

        info_layout = QVBoxLayout()
        name_label = QLabel(f"👤 {candidate.get('name', 'Candidate')}")
        name_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        name_label.setStyleSheet("background: transparent; border: none;")

        role_label = QLabel(f"💼 {candidate.get('current_role', 'N/A')}  |  ⏳ {candidate.get('total_experience', 'N/A')}")
        role_label.setStyleSheet("color: #b2bec3; font-size: 12px; background: transparent; border: none;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(role_label)
        info_layout.addStretch()

        stats_layout = QHBoxLayout()
        stats = [
            (str(summary["total_questions"]), "Questions"),
            (f"{avg_score}/10", "Avg Score"),
            (analysis.get("suggested_role_level", "N/A"), "Level"),
        ]
        for val, label in stats:
            stat_frame = QFrame()
            stat_frame.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 10px; padding: 5px;")
            stat_layout_v = QVBoxLayout(stat_frame)
            stat_layout_v.setContentsMargins(15, 10, 15, 10)

            val_label = QLabel(val)
            val_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
            val_label.setAlignment(Qt.AlignCenter)
            val_label.setStyleSheet("background: transparent; border: none;")

            lbl_label = QLabel(label)
            lbl_label.setAlignment(Qt.AlignCenter)
            lbl_label.setStyleSheet("color: #b2bec3; font-size: 10px; background: transparent; border: none;")

            stat_layout_v.addWidget(val_label)
            stat_layout_v.addWidget(lbl_label)
            stats_layout.addWidget(stat_frame)

        info_layout.addLayout(stats_layout)
        hero_layout.addLayout(info_layout)

        score_layout = QVBoxLayout()
        score_layout.setAlignment(Qt.AlignCenter)

        score_circle = ScoreCircle(avg_score, 90)
        score_layout.addWidget(score_circle, alignment=Qt.AlignCenter)

        verdict_colors = {
            "Highly Recommended": "#4caf50",
            "Recommended": "#8bc34a",
            "Consider": "#ff9800",
            "Not Recommended": "#f44336"
        }
        v_color = verdict_colors.get(verdict, "#ff9800")

        verdict_label = QLabel(verdict)
        verdict_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        verdict_label.setAlignment(Qt.AlignCenter)
        verdict_label.setStyleSheet(f"color: {v_color}; background: transparent; border: none;")
        score_layout.addWidget(verdict_label)

        hero_layout.addLayout(score_layout)
        self.results_main_layout.addWidget(hero)

        # ===== STRENGTHS & IMPROVEMENTS =====
        si_layout = QHBoxLayout()
        strengths = analysis.get("top_strengths", [])
        improvements = analysis.get("key_improvements", [])

        s_frame = self.create_list_card("🌟 Top Strengths", strengths, "#4caf50", "#1b2e1b")
        i_frame = self.create_list_card("🔧 Key Improvements", improvements, "#ff9800", "#2d2200")

        si_layout.addWidget(s_frame)
        si_layout.addWidget(i_frame)
        self.results_main_layout.addLayout(si_layout)

        # ===== RECOMMENDATION =====
        rec_frame = QFrame()
        rec_frame.setStyleSheet("QFrame { background: #16213e; border-radius: 12px; border: 1px solid #0f3460; }")
        rec_layout = QVBoxLayout(rec_frame)
        rec_layout.setContentsMargins(20, 15, 20, 15)

        rec_title = QLabel("📋 Hiring Recommendation")
        rec_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        rec_title.setStyleSheet("background: transparent; border: none;")
        rec_layout.addWidget(rec_title)

        rec_text = QLabel(analysis.get("hiring_recommendation", ""))
        rec_text.setWordWrap(True)
        rec_text.setStyleSheet("color: #b2bec3; font-size: 11px; background: transparent; border: none; line-height: 1.5;")
        rec_layout.addWidget(rec_text)
        self.results_main_layout.addWidget(rec_frame)

        # ===== Q&A SUMMARY =====
        qa_title = QLabel("📝 Question-wise Performance")
        qa_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        qa_title.setStyleSheet("background: transparent; border: none;")
        self.results_main_layout.addWidget(qa_title)

        for i, qa in enumerate(qa_pairs, 1):
            qa_card = self.create_qa_card(i, qa)
            self.results_main_layout.addWidget(qa_card)

        self.results_main_layout.addStretch()

    def create_list_card(self, title, items, color, bg_color):
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {bg_color}; border-radius: 12px; border: 1px solid {color}44; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        layout.addWidget(title_label)

        for item in items:
            item_label = QLabel(f"• {item}")
            item_label.setWordWrap(True)
            item_label.setStyleSheet("color: #dfe6e9; font-size: 11px; background: transparent; border: none;")
            layout.addWidget(item_label)

        if not items:
            na_label = QLabel("• N/A")
            na_label.setStyleSheet("color: #636e72; font-size: 11px; background: transparent; border: none;")
            layout.addWidget(na_label)

        return frame

    def create_qa_card(self, num, qa):
        q = qa["question"]
        answer = qa.get("answer", "N/A")
        eval_data = qa.get("evaluation", {})
        score = eval_data.get("score", 0)

        color = "#f44336"
        if score >= 8: color = "#4caf50"
        elif score >= 6: color = "#ff9800"
        elif score >= 4: color = "#ff6b35"

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: #16213e;
                border-radius: 10px;
                border-left: 4px solid {color};
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)

        score_label = QLabel(f"{score}")
        score_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        score_label.setFixedSize(45, 45)
        score_label.setAlignment(Qt.AlignCenter)
        score_label.setStyleSheet(f"color: white; background: {color}; border-radius: 22px; border: none;")
        layout.addWidget(score_label)

        content_layout = QVBoxLayout()

        q_text = QLabel(f"Q{num}: {q.get('question', '')[:100]}{'...' if len(q.get('question', '')) > 100 else ''}")
        q_text.setFont(QFont("Segoe UI", 10, QFont.Bold))
        q_text.setWordWrap(True)
        q_text.setStyleSheet("background: transparent; border: none;")
        content_layout.addWidget(q_text)

        meta = QLabel(f"Category: {q.get('category', 'N/A')}  |  Skill: {q.get('skill_tested', 'N/A')}  |  Rating: {eval_data.get('rating', 'N/A')}")
        meta.setStyleSheet("color: #b2bec3; font-size: 10px; background: transparent; border: none;")
        content_layout.addWidget(meta)

        if answer and answer != "(Skipped)":
            ans_preview = answer[:80] + "..." if len(answer) > 80 else answer
            ans_label = QLabel(f"Answer: {ans_preview}")
            ans_label.setStyleSheet("color: #74b9ff; font-size: 10px; background: transparent; border: none;")
            ans_label.setWordWrap(True)
            content_layout.addWidget(ans_label)

        layout.addLayout(content_layout)
        return frame

    def open_pdf(self):
        if self.pdf_path and os.path.exists(self.pdf_path):
            system = platform.system()
            if system == "Windows":
                os.startfile(self.pdf_path)
            elif system == "Darwin":
                subprocess.run(["open", self.pdf_path])
            else:
                subprocess.run(["xdg-open", self.pdf_path])
        else:
            print(f"[PDF] File not found: {self.pdf_path}")