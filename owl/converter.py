from dataclasses import dataclass

import cv2
from cv2 import Mat
import numpy as np
from hilbertcurve.hilbertcurve import HilbertCurve


@dataclass
class Converter:
    side_length: int

    def convert(self, frame: Mat) -> np.ndarray:
        # grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # make square
        frame = self._make_square(frame)

        # resize
        frame = cv2.resize(frame, (self.side_length, self.side_length))

        # hilbert walk
        sequence = self._hilbert_walk(frame)
        return sequence

    @staticmethod
    def _make_square(frame: Mat) -> Mat:
        height, width = frame.shape[:2]
        if width < height:
            height_offset = (height - width) // 2
            width_offset = 0
        else:
            height_offset = 0
            width_offset = (width - height) // 2
        
        side_length = min(width, height)
        return frame[
            height_offset : height_offset + side_length,
            width_offset : width_offset + side_length,
        ]
    
    @staticmethod
    def _hilbert_walk(frame: Mat) -> np.ndarray:
        side_length = frame.shape[0]

        curve = HilbertCurve(p=side_length - 1, n=2)
        return np.array(
            [
                frame[tuple(curve.point_from_distance(i))]
                for i in range(side_length ** 2)
            ]
        )
        
