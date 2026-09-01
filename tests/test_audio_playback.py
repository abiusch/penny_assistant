"""Unit tests for the cross-platform audio-output helper (Phase 5 Week 14).

Pure/mocked — no audio hardware needed. Locks the OS->command mapping and the
loud-on-unknown-platform contract BEFORE the helper is wired into the TTS
adapters. The adapters emit MP3, so each platform's command must be MP3-capable
(afplay/mpg123/ffplay), not a PCM/WAV-only tool (aplay/paplay/winsound).
"""
import subprocess
from unittest import mock

import pytest

from adapters.audio.playback import (
    build_playback_command,
    play_audio_file,
    UnsupportedPlatformError,
)

FILE = "/tmp/example.mp3"


def _patch_system(value):
    return mock.patch("adapters.audio.playback.platform.system", return_value=value)


class TestBuildPlaybackCommand:
    def test_darwin_uses_afplay(self):
        with _patch_system("Darwin"):
            assert build_playback_command(FILE) == ["afplay", FILE]

    def test_linux_uses_mpg123(self):
        with _patch_system("Linux"):
            assert build_playback_command(FILE) == ["mpg123", "-q", FILE]

    def test_windows_uses_ffplay(self):
        with _patch_system("Windows"):
            assert build_playback_command(FILE) == [
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", FILE,
            ]

    def test_unknown_platform_raises_naming_the_value(self):
        with _patch_system("Plan9"):
            with pytest.raises(UnsupportedPlatformError) as exc:
                build_playback_command(FILE)
        # the unresolved platform.system() value must appear in the message
        assert "Plan9" in str(exc.value)


class TestPlayAudioFile:
    """Thin blocking wrapper: subprocess.run(build_playback_command(...)) -> bool."""

    def test_returns_true_on_success(self):
        with _patch_system("Darwin"), \
                mock.patch("adapters.audio.playback.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
            assert play_audio_file(FILE) is True
            run.assert_called_once()
            # faithful: it plays exactly the built command
            assert run.call_args.args[0] == ["afplay", FILE]

    def test_returns_false_on_nonzero_returncode(self):
        with _patch_system("Darwin"), \
                mock.patch("adapters.audio.playback.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
            assert play_audio_file(FILE) is False

    def test_returns_false_when_player_binary_missing(self):
        # e.g. mpg123 not installed -> FileNotFoundError -> graceful False (soft)
        with _patch_system("Linux"), \
                mock.patch("adapters.audio.playback.subprocess.run",
                           side_effect=FileNotFoundError):
            assert play_audio_file(FILE) is False

    def test_returns_false_on_unsupported_platform(self):
        # convenience wrapper never raises: matches the adapters' _play_audio_file
        # contract (loud signal lives in build_playback_command, tested above).
        with _patch_system("Plan9"):
            assert play_audio_file(FILE) is False
