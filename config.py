import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY nahi mili! .env file check karo")

# Model Settings
GPT_MODEL = "llama-3.3-70b-versatile"  # GPT-4o jitna powerful, FREE!
WHISPER_MODEL = "whisper-large-v3"      # Groq ka fast whisper

# Baaki settings same rahengi
MAX_QUESTIONS = 7
ANSWER_TIME_LIMIT = 120
AUDIO_SAMPLE_RATE = 16000
REPORTS_DIR = "reports"
CAMERA_INDEX = 0
