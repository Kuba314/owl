from dataclasses import dataclass

import cv2

from owl.frequency_curve import FrequencyCurve
from owl.types import Frame

from ..utils import make_square
from .base import Sine, SineConverter


@dataclass
class CurveConverter(SineConverter):
    frequency_curve: FrequencyCurve

    def _extract_sines(self, frame: Frame) -> list[Sine]:
        frame = make_square(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

        side_length = self.frequency_curve.side_length
        resized_frame = cv2.resize(
            frame, (side_length, side_length), interpolation=cv2.INTER_AREA
        )
        self.emit("new-input-frame", frame)
        self.emit("new-converter-frame", resized_frame)

        return [
            Sine(frequency=freq, volume=resized_frame[y][x] / 255)
            for (x, y), freq in self.frequency_curve
        ]
