import io
import sys
import tempfile

# Python version compatibility check
if sys.version_info >= (3, 13):
    import warnings
    warnings.warn(
        "Python 3.13+ detected. OpenAI Whisper and audio libraries may have compatibility issues. "
        "Consider using Python 3.11 for better stability.",
        UserWarning,
        stacklevel=2
    )

try:
    import whisper  # type: ignore
except Exception:
    whisper = None

class WhisperSTT:
    def __init__(self, config):
        self.config = config or {}
        self.model_name = (self.config.get("stt") or {}).get("model", "base")
        self._model = None
        if whisper:
            try:
                self._model = whisper.load_model(self.model_name)
            except Exception:
                self._model = None

    def transcribe(self, audio_bytes: bytes):
        # default safe return
        empty = {"text": "", "confidence": 0.0, "segments": []}
        if not audio_bytes:
            return empty
        if not self._model:
            return empty
        # Try to treat bytes as a valid audio file by writing to temp
        # Whisper can handle many formats; we let it sniff file type.
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name

            try:
                result = self._model.transcribe(tmp_path, fp16=False) or {}
                text = (result.get("text") or "").strip()
                segs = result.get("segments") or []
                # Whisper doesn't provide a simple global confidence; estimate from avg no_speech_prob if present
                conf = 1.0
                if segs:
                    probs = []
                    for s in segs:
                        # lower no_speech_prob implies more confident speech; invert crudely
                        nsp = s.get("no_speech_prob")
                        if isinstance(nsp, (int, float)):
                            probs.append(1.0 - max(0.0, min(1.0, nsp)))
                    if probs:
                        conf = sum(probs) / len(probs)
                return {"text": text, "confidence": float(conf), "segments": segs}
            finally:
                # Clean up temporary file
                try:
                    import os
                    os.unlink(tmp_path)
                except Exception:
                    pass  # Ignore cleanup errors
        except Exception:
            return empty
