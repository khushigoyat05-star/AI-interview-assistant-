# 🎯 AI Interview Assistant

Ek smart Python desktop app jo aapke resume ke basis par personalized interview leta hai!

---

## ✨ Features

- 📄 **PDF Resume Upload** - Resume upload karo, AI automatically skills extract karega
- 🤖 **AI-Powered Questions** - GPT-4 se custom interview questions generate hote hain
- 📹 **Live Camera Feed** - Webcam se face dikhta hai interview ke dauran
- 🎤 **Voice Recording** - Microphone se answer record karo
- 📝 **Auto Transcription** - OpenAI Whisper se audio → text
- ⭐ **AI Evaluation** - GPT-4 se har answer evaluate hota hai
- 📊 **PDF Report** - Professional PDF report generate hoti hai

---

## 🛠️ Setup

### Step 1: Dependencies Install Karo

```bash
cd ai_interview_assistant
pip install -r requirements.txt
```

**Note**: PyAudio ke liye system dependencies chahiye:
- **Windows**: `pip install pyaudio` (usually works directly)
- **Mac**: `brew install portaudio && pip install pyaudio`
- **Linux**: `sudo apt-get install portaudio19-dev && pip install pyaudio`

### Step 2: OpenAI API Key Set Karo

`config.py` file mein apni API key daalo:

```python
OPENAI_API_KEY = "sk-your-actual-api-key-here"
```

> OpenAI API key yahan se lo: https://platform.openai.com/api-keys

### Step 3: App Chalaao

```bash
python main.py
```

---

## 📁 Project Structure

```
ai_interview_assistant/
├── main.py                     # App entry point
├── config.py                   # API keys & settings
├── requirements.txt            # Python dependencies
├── modules/
│   ├── resume_parser.py       # PDF → skills extract (GPT-4)
│   ├── question_gen.py        # Interview questions generate (GPT-4)
│   ├── speech_handler.py      # Audio record + Whisper transcribe
│   ├── evaluator.py           # Answer evaluate + final report data
│   ├── report_gen.py          # PDF report generate (ReportLab)
│   └── camera_handler.py      # Webcam feed (OpenCV)
├── ui/
│   ├── main_window.py         # Home screen (resume upload)
│   ├── interview_screen.py    # Interview screen (camera + Q&A)
│   └── report_screen.py       # Report screen (results + PDF download)
└── reports/                    # Generated PDF reports yahan save hongi
```

---

## 🔄 App Flow

```
1. Home Screen
   └─→ PDF Resume Upload
       └─→ AI Skills Extract (GPT-4)
           └─→ Questions Generate (GPT-4)

2. Interview Screen (Start button click karo)
   └─→ Camera ON
       └─→ Question Display
           └─→ Record Button → Answer Record
               └─→ Whisper Transcription
                   └─→ GPT-4 Evaluation
                       └─→ Next Question...

3. Report Screen (Interview khatam hone par)
   └─→ Final Analysis (GPT-4)
       └─→ PDF Report Generate
           └─→ Results Display + Download
```

---

## ⚙️ Configuration (config.py)

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_QUESTIONS` | 7 | Kitne questions puchne hain |
| `ANSWER_TIME_LIMIT` | 120 | Answer time limit (seconds) |
| `CAMERA_INDEX` | 0 | Webcam index (0 = default) |
| `GPT_MODEL` | gpt-4 | GPT model version |
| `WHISPER_MODEL` | whisper-1 | Whisper model |

---

## 🐛 Common Issues

**PyAudio install nahi ho raha?**
```bash
# Windows
pip install pipwin
pipwin install pyaudio

# Linux
sudo apt-get install python3-pyaudio
```

**Camera nahi dikh rahi?**
- `config.py` mein `CAMERA_INDEX = 1` try karo

**OpenAI Error?**
- API key check karo
- Internet connection check karo
- OpenAI account mein credits check karo

---

## 📋 Requirements

- Python 3.8+
- Webcam
- Microphone
- OpenAI API Key (GPT-4 access chahiye)
- Internet Connection

---

*Built with ❤️ using PyQt5, OpenAI, OpenCV & ReportLab*
