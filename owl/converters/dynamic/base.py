from abc import abstractmethod
from collections import deque
from dataclasses import dataclass, field
import logging

import numpy as np

from owl.types import Frame, Signal

from ..base import BaseConverter

logger = logging.getLogger("converter")


@dataclass(kw_only=True)
class DynamicConverter(BaseConverter):
    """Generates multiple different tones per frame"""

    ms_per_frame: int  # actual ms per frame will be more if sound cue provided
    sound_cue: list[float] | None = None
    ms_between_new_frames: float = 1000 / 30  # 30 FPS is a reasonable assumption

    _sound_cue_queue: list[float] = field(default_factory=list, init=False)
    _audio_samples_queue: deque[float] = field(default_factory=deque, init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self._sound_cue_duration_ms = (
            len(self.sound_cue) / self._audio_stream.sample_rate * 1000
            if self.sound_cue is not None
            else 0
        )

    @abstractmethod
    def convert_frame(self, frame: Frame) -> Signal:
        ...

    def get_next_soundgen_samples(self, count: int) -> np.ndarray:
        def popleft_or(deq: deque, default=None):
            if not len(deq):
                return default
            return deq.popleft()

        return np.array(
            [popleft_or(self._audio_samples_queue, 0.0) for _ in range(count)]
        )

    def on_new_frame(self, frame: Frame) -> None:
        # do nothing if we can afford to wait for the next frame
        if (
            1000 * len(self._audio_samples_queue) / self.sample_rate
            > self.ms_between_new_frames
        ):
            return

        # queue sound cue
        if self.sound_cue is not None:
            logger.debug("Inserting sound cue")
            self._sound_cue_queue.extend(self.sound_cue)

        logger.debug("Updating dynamic soundgen")
        self._audio_samples_queue.extend(self.convert_frame(frame))

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

        return np.concatenate(
            [ret, self.get_next_soundgen_samples(remaining_sample_count)]
        )
