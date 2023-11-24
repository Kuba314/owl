from collections import deque
from dataclasses import dataclass
import logging

import cv2
import numpy as np

from owl.soundgen import MultiFreqGen
from owl.types import Frame

from .base import DynamicConverter

logger = logging.getLogger("converter")


@dataclass
class ScanConverter(DynamicConverter):
    strip_count: int
    frequencies: list[float]

    def __post_init__(self) -> None:
        super().__post_init__()

        self._sound_gen = MultiFreqGen(self.frequencies)
        self._audio_samples_queue = deque[float]()
        self._samples_per_strip = int(
            self.ms_per_frame / 1000 * self._sound_gen.sample_rate / self.strip_count
        )

    def get_next_soundgen_samples(self, count: int) -> np.ndarray:
        def popleft_or(deq: deque, default=None):
            if not len(deq):
                return default
            return deq.popleft()

        return np.array(
            [popleft_or(self._audio_samples_queue, 0.0) for _ in range(count)]
        )


class HorizontalScanConverter(ScanConverter):
    def update_soundgen(self, frame: Frame) -> None:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, (self.strip_count, len(self.frequencies)))

        for i in range(self.strip_count):
            volumes = frame[:][i] / 255
            logger.debug(f"strip[{i}] volumes: {volumes}")
            self._sound_gen.set_volumes(volumes, backoff=0.01)
            self._audio_samples_queue.extend(
                self._sound_gen.get_next_samples(self._samples_per_strip)
            )


class VerticalScanConverter(ScanConverter):
    def update_soundgen(self, frame: Frame) -> None:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, (len(self.frequencies), self.strip_count))

        for i in range(self.strip_count):
            volumes = frame[i] / 255
            logger.debug(f"strip[{i}] volumes: {volumes}")
            self._sound_gen.set_volumes(volumes, backoff=0.01)
            self._audio_samples_queue.extend(
                self._sound_gen.get_next_samples(self._samples_per_strip)
            )
