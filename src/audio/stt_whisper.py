import whisper
import tempfile
import os

model = whisper.load_model("base")  # consider tiny/base for speed

def transcribe_audio(audio_data: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_data)
        temp_audio_path = temp_audio.name
    try:
        result = model.transcribe(temp_audio_path)
        return result.get('text', '').strip()
    finally:
        os.remove(temp_audio_path)
