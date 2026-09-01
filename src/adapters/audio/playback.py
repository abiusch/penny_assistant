"""Cross-platform audio-output primitives (Phase 5 Week 14, first slice).

Centralizes the OS-specific playback command that the TTS adapters previously
hardcoded as ``["afplay", <file>]``. The adapters emit **MP3**, so every
platform's command must be MP3-capable — ``afplay`` (macOS), ``mpg123`` (Linux),
``ffplay`` (Windows) — NOT a PCM/WAV-only tool like ``aplay``/``paplay``/
``winsound``.

Failure model (two tiers):
  * **Unknown platform** -> ``build_playback_command`` raises
    ``UnsupportedPlatformError`` (loud), so a missing port is obvious during
    development rather than a silent mute.
  * **Known platform, player binary missing** -> a runtime ``FileNotFoundError``
    at ``subprocess`` time, which callers already catch and degrade to silence.

The interruptible TTS adapters call ``build_playback_command`` directly (keeping
their own Popen/poll/terminate barge-in logic); ``play_audio_file`` is a thin
blocking convenience for simple callers.
"""
import platform
import subprocess
from typing import List


class UnsupportedPlatformError(RuntimeError):
    """Raised when no audio playback command is defined for the host platform."""


def build_playback_command(file_path: str) -> List[str]:
    """Return the platform-appropriate argv to play an MP3 ``file_path``.

    Raises ``UnsupportedPlatformError`` (naming the unresolved
    ``platform.system()`` value) for any platform without a defined command.
    """
    system = platform.system()
    if system == "Darwin":
        return ["afplay", file_path]
    if system == "Linux":
        return ["mpg123", "-q", file_path]
    if system == "Windows":
        return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path]
    raise UnsupportedPlatformError(
        f"No audio playback command defined for platform: {system!r}"
    )


def play_audio_file(file_path: str) -> bool:
    """Blocking convenience: play ``file_path`` to completion, return success.

    Thin wrapper over ``subprocess.run(build_playback_command(...))``. Never
    raises — returns ``False`` on any failure (unsupported platform, missing
    player binary, non-zero exit), matching the adapters' ``_play_audio_file``
    contract. Callers needing barge-in should use ``build_playback_command``
    directly with their own process handling.
    """
    try:
        result = subprocess.run(
            build_playback_command(file_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False
