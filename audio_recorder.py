import pyaudio
import wave
import os
import tempfile
import threading
from groq import Groq
from config import GROQ_API_KEY, AUDIO_SAMPLE_RATE, WHISPER_MODEL

# Groq client
client = Groq(api_key=GROQ_API_KEY)


class AudioRecorder:
    """Real-time audio recorder jo PyAudio use karta hai"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.record_thread = None
        
        # Audio settings
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = AUDIO_SAMPLE_RATE
        self.chunk = 1024
    
    def start_recording(self):
        """Recording shuru karo"""
        self.frames = []
        self.is_recording = True
        
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.daemon = True
        self.record_thread.start()
        print("[Audio] Recording shuru ho gayi...")
    
    def _record_loop(self):
        """Background mein audio capture karta raho"""
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"[Audio] Recording error: {e}")
                break
    
    def stop_recording(self) -> str:
        """Recording band karo aur audio file path return karo"""
        self.is_recording = False
        
        if self.record_thread:
            self.record_thread.join(timeout=2)
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if not self.frames:
            print("[Audio] Koi audio capture nahi hua!")
            return None
        
        # Temp WAV file mein save karo
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        
        print(f"[Audio] Recording save hui: {temp_path}")
        return temp_path
    
    def cleanup(self):
        """Resources free karo"""
        if self.audio:
            self.audio.terminate()


def transcribe_audio(audio_file_path: str) -> str:
    """
    Groq Whisper API se audio ko text mein convert karo
    Returns: transcribed text string
    """
    if not audio_file_path or not os.path.exists(audio_file_path):
        return ""
    
    try:
        print("[Whisper] Audio transcribe ho rahi hai...")
        
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file,
                language="en"  # English ke liye, "hi" for Hindi
            )
        
        transcribed_text = transcript.text.strip()
        print(f"[Whisper] Transcription: {transcribed_text[:100]}...")
        
        # Temp file delete karo
        os.unlink(audio_file_path)
        
        return transcribed_text
        
    except Exception as e:
        print(f"[Whisper] Transcription error: {str(e)}")
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)
        return ""


def record_and_transcribe(duration_callback=None) -> tuple:
    """
    Convenience function: record karo aur transcribe karo
    Returns: recorder_object - caller stop karega
    """
    recorder = AudioRecorder()
    recorder.start_recording()
    return recorder