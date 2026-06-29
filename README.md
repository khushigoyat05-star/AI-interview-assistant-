# 🎯 AI Interview Assistant

An intelligent Python-based desktop application that conducts personalized AI-powered interviews based on a candidate's resume.

---

## ✨ Features

* 📄 **PDF Resume Upload** – Upload a resume and the AI automatically extracts skills and relevant information.
* 🤖 **AI-Powered Interview Questions** – Generates personalized interview questions using AI.
* 📹 **Live Camera Monitoring** – Displays the candidate through the webcam during the interview.
* 🎤 **Voice Recording** – Records candidate responses through the microphone.
* 📝 **Automatic Speech-to-Text** – Converts spoken answers into text using OpenAI Whisper.
* ⭐ **AI Answer Evaluation** – Evaluates each answer and provides detailed feedback.
* 📊 **PDF Report Generation** – Generates a professional interview performance report.

---

# 🛠️ Installation

## Step 1: Install Dependencies

```bash
cd ai_interview_assistant
pip install -r requirements.txt
```

**Note:** PyAudio requires additional system dependencies.

### Windows

```bash
pip install pyaudio
```

### macOS

```bash
brew install portaudio
pip install pyaudio
```

### Linux

```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

---

## Step 2: Configure the API Key

Open the `config.py` file and add your API key.

```python
OPENAI_API_KEY = "your-api-key"
```

---

## Step 3: Run the Application

```bash
python main.py
```

---

# 📁 Project Structure

```text
ai_interview_assistant/
├── main.py                     # Application entry point
├── config.py                   # API keys and configuration
├── requirements.txt            # Project dependencies
├── modules/
│   ├── resume_parser.py        # Extract skills from resume
│   ├── question_gen.py         # Generate interview questions
│   ├── speech_handler.py       # Record audio and transcribe speech
│   ├── evaluator.py            # Evaluate answers
│   ├── report_gen.py           # Generate PDF reports
│   └── camera_handler.py       # Webcam management
├── ui/
│   ├── main_window.py          # Resume upload interface
│   ├── interview_screen.py     # Interview interface
│   └── report_screen.py        # Result and report screen
└── reports/                    # Generated PDF reports
```

---

# 🔄 Application Workflow

```text
1. Home Screen
   ↓
Resume Upload
   ↓
Resume Analysis
   ↓
Skill Extraction
   ↓
AI Question Generation

2. Interview Session
   ↓
Start Camera
   ↓
Display Question
   ↓
Record Candidate Response
   ↓
Speech-to-Text Conversion
   ↓
AI-Based Answer Evaluation
   ↓
Next Question

3. Interview Completed
   ↓
Performance Analysis
   ↓
Generate PDF Report
   ↓
Display Final Results
```

---

# ⚙️ Configuration

| Setting             | Default   | Description                                          |
| ------------------- | --------- | ---------------------------------------------------- |
| `MAX_QUESTIONS`     | 7         | Maximum number of interview questions                |
| `ANSWER_TIME_LIMIT` | 120       | Time limit per answer (seconds)                      |
| `CAMERA_INDEX`      | 0         | Default webcam index                                 |
| `GPT_MODEL`         | GPT-4     | AI model used for question generation and evaluation |
| `WHISPER_MODEL`     | whisper-1 | Speech-to-text model                                 |

---

# 🐞 Troubleshooting

### PyAudio Installation Issues

#### Windows

```bash
pip install pipwin
pipwin install pyaudio
```

#### Linux

```bash
sudo apt-get install python3-pyaudio
```

### Camera Not Detected

Try changing the webcam index in `config.py`.

```python
CAMERA_INDEX = 1
```

### API Errors

* Verify that the API key is correct.
* Ensure an active internet connection.
* Confirm that your API account has sufficient credits.

---

# 📋 Requirements

* Python 3.8 or later
* Webcam
* Microphone
* OpenAI API Key
* Internet Connection

---

# 🚀 Technologies Used

* Python
* OpenAI GPT
* OpenAI Whisper
* OpenCV
* PyQt5
* ReportLab
* PyAudio

---

# 📄 License

This project is intended for educational and portfolio purposes.

---

⭐ If you find this project useful, consider giving it a star on GitHub.

