from collections.abc import Iterator
import itertools

import cv2

from owl.curves import HilbertCurve
from owl.types import Frame

from ..utils import make_square
from .base import Sine, SineConverter


class HilbertSpreadConverter(SineConverter):
    """
    Combine hilbert curves of N orders, each mapping pixels
    to more spread frequencies
    """

    def __init__(self, base_freq: float, order: int, transient_duration: float):
        self._base_freq = base_freq
        self._order = order

        self._all_freqs = list(
            itertools.chain.from_iterable(
                self.generate_frequency_groups(base_freq, order)
            )
        )
        super().__init__(len(self._all_freqs), transient_duration=transient_duration)

    def _extract_sines(self, frame: Frame) -> list[Sine]:
        frame = make_square(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

        volumes: list[float] = []
        frames = []
        for side_length in (2**i for i in itertools.count()):
            resized_frame = cv2.resize(
                frame, (side_length, side_length), interpolation=cv2.INTER_AREA
            )
            frames.append(resized_frame)

            curve = HilbertCurve(order=side_length - 1)
            for point in curve.generate():
                volumes.extend(resized_frame[point] / 255)

        # notify("converter:outputs", frames)
        return [Sine(frequency=f, volume=v) for f, v in zip(self._all_freqs, volumes)]

    @staticmethod
    def generate_frequency_groups(
        base_freq: float, order: int
    ) -> Iterator[list[float]]:
        def spread(freq: float, ratio: float) -> list[float]:
            return [
                freq / ratio**2,
                freq / ratio,
                freq * ratio,
                freq * ratio**2,
            ]

        freqs = [base_freq]
        freq_ratio = 2.0
        for _ in range(order):
            yield freqs

            freq_ratio **= -4
            freqs = list(
                itertools.chain.from_iterable(
                    [spread(freq, freq_ratio) for freq in freqs]
                )
            )
