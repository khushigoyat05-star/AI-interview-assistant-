import pyaudio

p = pyaudio.PyAudio()
print("PyAudio OK")
print("Input devices found:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"  Device {i}: {info['name']}")
p.terminate()

import pyttsx3
try:
    engine = pyttsx3.init()
    engine.say("Test")
    engine.runAndWait()
    print("TTS OK")
except Exception as e:
    print(f"TTS Error: {e}")