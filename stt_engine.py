import whisper
import tempfile
import soundfile as sf
import numpy as np

SILENCE_THRESHOLD = 0.0005  # Lower = more sensitive. Was 0.002 but mic input is very quiet

def is_silence(audio_data, threshold=SILENCE_THRESHOLD):
    volume = np.abs(audio_data).mean()
    return volume < threshold

def transcribe_audio(audio_data):
    # Debug: Check audio properties
    volume = np.abs(audio_data).mean()
    max_amp = np.abs(audio_data).max()
    print(f"[STT Debug] Audio volume: {volume:.6f}, max: {max_amp:.4f}, threshold: {SILENCE_THRESHOLD}")

    if is_silence(audio_data):
        print(f"[STT Debug] Audio rejected as silence (volume {volume:.6f} < {SILENCE_THRESHOLD})")
        return None  # Skip transcription if the audio is mostly silence

    print(f"[STT Debug] Audio accepted, transcribing...")
    model = whisper.load_model("base")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        sf.write(tmp.name, audio_data, 16000)
        result = model.transcribe(tmp.name)
    print(f"[STT Debug] Transcription: '{result['text']}'")
    return result["text"].strip()

