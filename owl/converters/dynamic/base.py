from abc import abstractmethod
from collections import deque
from dataclasses import dataclass, field
import logging

import numpy as np

from owl.soundgen import Envelope
from owl.types import Frame, Signal

from ..base import BaseConverter


logger = logging.getLogger("converter")


@dataclass(kw_only=True)
class DynamicConverter(BaseConverter):
    """Generates multiple different tones per frame"""

    ms_per_frame: int  # actual ms per frame will be more if sound cue provided
    sound_cue: Signal | None = None
    ms_between_new_frames: float = 1000 / 30  # 30 FPS is a reasonable assumption

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

    def on_new_frame(self, frame: Frame) -> None:
        # do nothing if we can afford to wait for the next frame
        # three video frames should be enough time for new frame to be inserted into deque
        if (
            1000 * len(self._audio_samples_queue) / self.sample_rate
            > 3 * self.ms_between_new_frames
        ):
            return

        # queue sound cue
        if self.sound_cue is not None:
            logger.debug("Inserting sound cue")
            self._audio_samples_queue.extend(self.sound_cue)

        queue_ms_left = 1000 * len(self._audio_samples_queue) / self.sample_rate
        logger.debug(f"Converting new video frame with {queue_ms_left:.0f}ms to spare")

        signal = self.convert_frame(frame)
        env = Envelope(0.005, 0.001, 0.001, 0.8)
        signal = env.apply(signal, sample_rate=self.sample_rate)
        self._audio_samples_queue.extend(signal)

    def get_next_samples(self, count: int) -> Signal:
        def popleft_or(deq: deque, default=None):
            if not len(deq):
                return default
            return deq.popleft()

        return np.array(
            [popleft_or(self._audio_samples_queue, 0.0) for _ in range(count)]
        )
