from dataclasses import dataclass

import cv2

from owl.curves import Curve
from owl.types import Frame
from .base import ConstFreqConverter
from ..utils import make_square


@dataclass
class CurveConverter(ConstFreqConverter):
    curve: Curve

    def _extract_volumes(self, frame: Frame) -> list[float]:
        frame = make_square(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

        side_length = self.curve.side_length
        resized_frame = cv2.resize(
            frame, (side_length, side_length), interpolation=cv2.INTER_AREA
        )

        return [resized_frame[y][x] / 255 for x, y in self.curve.generate()]
