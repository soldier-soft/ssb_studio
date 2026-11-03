"""Sound cue service supporting asynchronous procedural audio on Windows."""

import logging
import sys
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class SoundService:
    """Provides non-blocking audio cues for timer warnings, transitions, and completions."""

    def __init__(self, enabled: bool = True, volume: int = 80) -> None:
        self.enabled = enabled
        self.volume = volume

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)

    def set_volume(self, volume: int) -> None:
        self.volume = max(0, min(100, int(volume)))

    def play_cue(self, cue_name: str) -> None:
        """Trigger an asynchronous sound cue without stalling the GUI."""
        if not self.enabled or self.volume <= 0:
            return

        thread = threading.Thread(
            target=self._play_sync,
            args=(cue_name,),
            daemon=True,
            name=f"SoundCue-{cue_name}",
        )
        thread.start()

    def _play_sync(self, cue_name: str) -> None:
        if sys.platform != "win32":
            return

        try:
            import winsound

            if cue_name == "countdown":
                # Short high tick
                winsound.Beep(950, 45)
            elif cue_name == "transition":
                # Double chime for phase advancement
                winsound.Beep(660, 70)
                winsound.Beep(880, 100)
            elif cue_name == "bell":
                # Triad completion fan-fare
                winsound.Beep(523, 90)
                winsound.Beep(659, 90)
                winsound.Beep(784, 160)
            elif cue_name == "click":
                winsound.Beep(1200, 25)
        except Exception as e:
            logger.debug(f"Sound cue playback skipped: {e}")
