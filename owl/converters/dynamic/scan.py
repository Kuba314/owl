from dataclasses import dataclass
import logging

import cv2
import numpy as np

from owl.events import notify
from owl.soundgen import MultiSineGen
from owl.types import Frame, Signal

from .base import DynamicConverter


logger = logging.getLogger("converter")


@dataclass
class ScanConverter(DynamicConverter):
    """Scan image with strips assigning frequencies to each strip"""

    strip_count: int
    frequencies: list[float]

    def __post_init__(self) -> None:
        super().__post_init__()

        self._sound_gen = MultiSineGen(self.frequencies)
        self._samples_per_strip = int(
            self.ms_per_frame / 1000 * self._sound_gen.sample_rate / self.strip_count
        )


class HorizontalScanConverter(ScanConverter):
    """Scan image horizontally, each strip being a vertical line"""

    def convert_frame(self, frame: Frame) -> Signal:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        notify("converter:frame:pre", frame)
        frame = cv2.resize(frame, (self.strip_count, len(self.frequencies)))
        notify("converter:frame:post", frame)

        signal = np.empty(shape=[0], dtype=np.float32)
        for i in range(self.strip_count):
            volumes = frame[:, i] / 255  # type: ignore
            logger.debug(f"strip[{i}] volumes: {volumes}")
            self._sound_gen.set_volumes(volumes, backoff=0.01)
            signal = np.concatenate(
                [signal, self._sound_gen.get_next_samples(self._samples_per_strip)]
            )
        return signal


class VerticalScanConverter(ScanConverter):
    """Scan image vertically, each strip being a horizontal line"""

    def convert_frame(self, frame: Frame) -> Signal:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        notify("converter:frame:pre", frame)
        frame = cv2.resize(frame, (len(self.frequencies), self.strip_count))
        notify("converter:frame:post", frame)

        signal = np.empty(shape=[0], dtype=np.float32)
        for i in range(self.strip_count):
            volumes = frame[self.strip_count - i - 1] / 255
            logger.debug(f"strip[{i}] volumes: {volumes}")
            self._sound_gen.set_volumes(volumes, backoff=0.01)
            signal = np.concatenate(
                [signal, self._sound_gen.get_next_samples(self._samples_per_strip)]
            )
        return signal


class CircularScanConverter(ScanConverter):
    """Scan image with circles with increasing size

    Center pixel of the resized image is purposely left unscanned.
    """

    def convert_frame(self, frame: Frame) -> Signal:
        center = self.strip_count
        side_length = self.strip_count * 2 + 1

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        notify("converter:frame:pre", frame)
        frame = cv2.resize(frame, (side_length, side_length))
        notify("converter:frame:post", frame)

        signal = np.empty(shape=[0], dtype=np.float32)
        for i in range(1, self.strip_count + 1):
            angles = np.linspace(0, 360, len(self.frequencies), endpoint=False)
            xs = np.rint(i * np.cos(angles * np.pi / 180) + center).astype(int)
            ys = np.rint(i * np.sin(angles * np.pi / 180) + center).astype(int)
            volumes = frame[ys, xs] / 255  # type: ignore
            logger.debug(f"strip[{i}] volumes: {volumes}")

            self._sound_gen.set_volumes(volumes, backoff=0.01)
            signal = np.concatenate(
                [signal, self._sound_gen.get_next_samples(self._samples_per_strip)]
            )

        return signal
