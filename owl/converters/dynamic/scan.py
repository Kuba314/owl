from dataclasses import dataclass
import logging
from typing import cast

import cv2
import numpy as np

from owl.converters.utils import grayscale
from owl.soundgen import MultiSineGen
from owl.types import Frame, Signal

from .base import DynamicConverter


logger = logging.getLogger("scan_converter")


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
        frame = grayscale(frame)
        self.emit("new-input-frame", frame)
        frame = cast(Frame, cv2.resize(frame, (self.strip_count, len(self.frequencies))))
        self.emit("new-converter-frame", frame)

        signal = np.empty(shape=[0], dtype=np.float32)
        for i in range(self.strip_count):
            # take i-th column, bottom to top
            volumes = frame[::-1, i] / 255
            logger.debug(f"strip[{i}] volumes: {' '.join(f'{v:.02f}' for v in volumes)}")
            self._sound_gen.set_volumes(volumes, transient_duration=0.01)
            signal = np.concatenate(
                [signal, self._sound_gen.get_next_samples(self._samples_per_strip)]
            )
        return signal


class VerticalScanConverter(ScanConverter):
    """Scan image vertically, each strip being a horizontal line"""

    def convert_frame(self, frame: Frame) -> Signal:
        frame = grayscale(frame)
        self.emit("new-input-frame", frame)
        frame = cast(Frame, cv2.resize(frame, (len(self.frequencies), self.strip_count)))
        self.emit("new-converter-frame", frame)

        signal = np.empty(shape=[0], dtype=np.float32)
        for i in range(self.strip_count):
            # take i-th row from bottom
            volumes = frame[self.strip_count - i - 1] / 255
            logger.debug(f"strip[{i}] volumes: {' '.join(f'{v:.02f}' for v in volumes)}")
            self._sound_gen.set_volumes(volumes, transient_duration=0.01)
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

        frame = grayscale(frame)
        self.emit("new-input-frame", frame)
        frame = cast(Frame, cv2.resize(frame, (side_length, side_length)))
        self.emit("new-converter-frame", frame)

        signal = np.empty(shape=[0], dtype=np.float32)
        for i in range(1, self.strip_count + 1):
            angles = np.linspace(0, 360, len(self.frequencies), endpoint=False)
            xs = np.rint(i * np.cos(angles * np.pi / 180) + center).astype(int)
            ys = np.rint(i * np.sin(angles * np.pi / 180) + center).astype(int)
            volumes = frame[ys, xs] / 255
            logger.debug(f"strip[{i}] volumes: {' '.join(f'{v:.02f}' for v in volumes)}")

            self._sound_gen.set_volumes(volumes, transient_duration=0.01)
            signal = np.concatenate(
                [signal, self._sound_gen.get_next_samples(self._samples_per_strip)]
            )

        return signal
