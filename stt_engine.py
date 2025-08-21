import whisper
import tempfile
import soundfile as sf
import numpy as np

SILENCE_THRESHOLD = 0.005  # Lower = more sensitive. Raise if you're getting false positives.

def is_silence(audio_data, threshold=SILENCE_THRESHOLD):
    volume = np.abs(audio_data).mean()
    return volume < threshold

def transcribe_audio(audio_data):
    if is_silence(audio_data):
        return None  # Skip transcription if the audio is mostly silence

    model = whisper.load_model("base")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        sf.write(tmp.name, audio_data, 16000)
        result = model.transcribe(tmp.name)
    return result["text"].strip()

