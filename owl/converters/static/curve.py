from collections.abc import Sequence
from dataclasses import dataclass

import cv2

from owl.curves import Curve
from owl.events import notify
from owl.types import Frame

from ..utils import make_square
from .base import Sine, SineConverter


class CurveConverter(SineConverter):
    def __init__(self, curve: Curve, frequencies: Sequence[float], sample_rate: int):
        super().__init__(sine_count=len(frequencies), sample_rate=sample_rate)
        self.curve = curve
        self.frequencies = frequencies

    def _extract_sines(self, frame: Frame) -> list[Sine]:
        frame = make_square(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

        side_length = self.curve.side_length
        resized_frame = cv2.resize(
            frame, (side_length, side_length), interpolation=cv2.INTER_AREA
        )
        notify("converter:frame:pre", frame)
        notify("converter:frame:post", resized_frame)

        return [
            Sine(frequency=f, volume=resized_frame[y][x] / 255)
            for f, (x, y) in zip(self.frequencies, self.curve.generate())
        ]
