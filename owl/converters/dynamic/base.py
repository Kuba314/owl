from abc import abstractmethod
from dataclasses import dataclass, field
import logging
import time

import numpy as np

from owl.types import Frame, Signal

from ..base import BaseConverter

logger = logging.getLogger("converter")


@dataclass(kw_only=True)
class DynamicConverter(BaseConverter):
    """Generates multiple different tones per frame"""

    # actual ms per frame will be more if sound cue provided
    ms_per_frame: int
    sound_cue: list[float] | None = None

    _last_cue_timestamp: float = field(default=0.0, init=False)
    _sound_cue_queue: list[float] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self._sound_cue_duration_ms = (
            len(self.sound_cue) / self._audio_stream.sample_rate * 1000
            if self.sound_cue is not None
            else 0
        )

    @abstractmethod
    def update_soundgen(self, frame: Frame) -> None:
        ...

    @abstractmethod
    def get_next_soundgen_samples(self, count: int) -> np.ndarray:
        ...

    def on_new_frame(self, frame: Frame) -> None:
        now_ms = time.time() * 1000
        delay = self._sound_cue_duration_ms + self.ms_per_frame

        # do nothing if next frame scan is in the future
        if self._last_cue_timestamp + delay > now_ms:
            return

        self._last_cue_timestamp = now_ms

        # queue sound cue
        if self.sound_cue is not None:
            logger.debug("Inserting sound cue")
            self._sound_cue_queue.extend(self.sound_cue)

        logger.debug("Updating dynamic soundgen")
        self.update_soundgen(frame)

    def get_next_samples(self, count: int) -> Signal:
        # if requested sample count satisfied by sound cue queue, return that
        if count <= len(self._sound_cue_queue):
            ret = np.array(self._sound_cue_queue[:count])
            self._sound_cue_queue = self._sound_cue_queue[count:]
            return ret

        # else return rest of sound cue queue and also part of the actual frame
        remaining_sample_count = count - len(self._sound_cue_queue)
        ret = np.array(self._sound_cue_queue)
        self._sound_cue_queue.clear()

        return np.append(ret, self.get_next_soundgen_samples(remaining_sample_count))
