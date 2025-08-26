import io
import sys
from enum import Enum
from typing import Optional

# Python version compatibility check
if sys.version_info >= (3, 13):
    import warnings
    warnings.warn(
        "Python 3.13+ detected. Audio libraries (Whisper, WebRTC VAD, gTTS) may have compatibility issues. "
        "Consider using Python 3.11 for better stability.",
        UserWarning,
        stacklevel=2
    )
from core.stt.factory import STTFactory
from core.tts.factory import TTSFactory
from adapters.llm.factory import LLMFactory
from core.vad.webrtc_vad import SimpleVAD
from core.telemetry import Telemetry
from core.llm_router import load_config

class State(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"

class PipelineLoop:
    def __init__(self):
        self.cfg = load_config()
        self.llm = LLMFactory.from_config(self.cfg)
        self.stt = STTFactory.create(self.cfg)
        self.vad = SimpleVAD()
        self.tts = TTSFactory.create(self.cfg)
        self.telemetry = Telemetry()
        self.state = State.IDLE
        self.audio_buffer = io.BytesIO()
        self.barge_in_enabled = True

    def _route_tone(self, text: str) -> str:
        """Simple tone routing based on text content."""
        text_lower = text.lower()
        if any(word in text_lower for word in ["help", "please", "thank"]):
            return "helpful"
        elif any(word in text_lower for word in ["joke", "funny", "laugh"]):
            return "humorous"
        else:
            return "neutral"

    def start_listening(self):
        """Start the listening phase, buffer audio frames."""
        if self.state == State.IDLE:
            self.state = State.LISTENING
            self.audio_buffer = io.BytesIO()
            self.telemetry.log_event("listening_start")
            return True
        return False

    def feed_audio_frame(self, frame_bytes: bytes) -> bool:
        """Feed audio frame to VAD and buffer if voice detected."""
        if self.state != State.LISTENING:
            return False
        
        # Check if this frame contains voice
        is_voice = self.vad.feed_is_voice(frame_bytes)
        
        if is_voice:
            # Buffer the frame
            self.audio_buffer.write(frame_bytes)
            
        return is_voice

    def end_listening(self) -> Optional[str]:
        """End listening phase and transcribe buffered audio."""
        if self.state != State.LISTENING:
            return None
            
        self.state = State.THINKING
        self.telemetry.log_event("listening_end")
        
        # Get buffered audio bytes
        audio_bytes = self.audio_buffer.getvalue()
        
        if not audio_bytes:
            self.state = State.IDLE
            return None
            
        # Transcribe the audio
        try:
            stt_result = self.stt.transcribe(audio_bytes)
            text = stt_result.get("text", "").strip() if isinstance(stt_result, dict) else str(stt_result).strip()
            self.telemetry.log_event("stt_complete", {"text": text, "confidence": stt_result.get("confidence", 0.0) if isinstance(stt_result, dict) else 1.0})
            return text
        except Exception as e:
            self.telemetry.log_event("stt_error", {"error": str(e)})
            self.state = State.IDLE
            return None

    def think(self, user_text: str) -> str:
        """Process user text through LLM and personality layers."""
        if self.state != State.THINKING:
            return ""
        
        tone = self._route_tone(user_text)
        self.telemetry.log_event("thinking_start", {"tone": tone})
        
        # Personality layer (optional): try to import; else fall back
        try:
            from core.personality import apply as apply_personality  # expect apply(text, tone) -> str
        except Exception:
            def apply_personality(txt, t): return f"[{t}] {txt}" if txt else "Say that again?"
        
        # Use LLM factory if available; otherwise echo
        try:
            # Try .complete() method first, fall back to .generate()
            if hasattr(self.llm, 'complete'):
                reply_raw = self.llm.complete(user_text or "Hello", tone=tone)
            else:
                reply_raw = self.llm.generate(user_text or "Hello")
        except Exception as e:
            self.telemetry.log_event("llm_error", {"error": str(e)})
            reply_raw = user_text or "Hello"
        
        reply = apply_personality(reply_raw, self.cfg.get("personality", {}))
        self.telemetry.log_event("thinking_complete", {"reply": reply})
        self.state = State.SPEAKING
        return reply

    def speak(self, text: str) -> bool:
        """Use TTS to speak the text, then return to IDLE."""
        if self.state != State.SPEAKING:
            return False
            
        self.telemetry.log_event("speaking_start")
        
        try:
            # Start TTS
            self.tts.speak(text)
            self.telemetry.log_event("speaking_complete")
        except Exception as e:
            self.telemetry.log_event("speaking_error", {"error": str(e)})
        
        # Return to IDLE state
        self.state = State.IDLE
        return True

    def handle_barge_in(self):
        """Handle barge-in behavior during speaking."""
        if self.state == State.SPEAKING and self.barge_in_enabled:
            # Stop current TTS
            try:
                if hasattr(self.tts, 'stop'):
                    self.tts.stop()
            except Exception:
                pass
            
            # Return to IDLE
            self.state = State.IDLE
            self.telemetry.log_event("barge_in")
            return True
        return False

    def get_state(self) -> State:
        """Get current pipeline state."""
        return self.state

def run_once() -> dict:
    """Legacy function for backwards compatibility."""
    cfg = load_config()
    llm = LLMFactory.from_config(cfg)
    stt = STTFactory.create(cfg)
    vad = SimpleVAD()
    tts = TTSFactory.create(cfg)
    telemetry = Telemetry()
    prompt = "Hello"
    reply = llm.generate(prompt)
    
    try:
        from core.personality import apply
        out = apply(reply, cfg.get("personality", {}))
    except Exception:
        out = f"[neutral] {reply}"
    
    try:
        tts.speak(out)
        audio_len = len(out.encode())  # Rough estimate
    except Exception:
        audio_len = 0
    
    return {"text": out, "audio_len": audio_len}

if __name__ == "__main__":
    print(run_once())
