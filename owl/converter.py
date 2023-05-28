from dataclasses import dataclass
from abc import ABC, abstractmethod
import itertools
from typing import Callable, Iterator

import cv2
from cv2 import Mat
from cv2 import resize
from owl.curves import hilbert_curve, peano_curve


class Converter(ABC):
    def preprocess_frame(self, frame: Mat) -> Mat:
        # grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # make square
        frame = self._make_square(frame)
        self.display_frame(frame, caption="Input")
        return frame

    def convert(self, frame: Mat) -> dict[float, float]:
        frame = self.preprocess_frame(frame)
        return self.convert_processed_frame(frame)

    @abstractmethod
    def convert_processed_frame(self, frame: Mat) -> dict[float, float]:
        ...

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
    def display_frame(frame: Mat, caption: str = "Frame") -> None:
        cv2.imshow(caption, frame)


@dataclass
class GenericCurveConverter(Converter):
    curve_order: int
    side_length: int
    curve_generator: Callable[[int], Iterator[tuple[int, int]]]

    def convert_processed_frame(self, frame: Mat) -> dict[float, float]:
        resized_frame = cv2.resize(
            frame, (self.side_length, self.side_length), interpolation=cv2.INTER_AREA
        )
        self.display_frame(resized_frame, caption="Resized Input")

        brightness_values = [
            resized_frame[y][x] / 256 for x, y in self.curve_generator(self.curve_order)
        ]
        return self.assign_frequencies(brightness_values)

    @abstractmethod
    def assign_frequencies(self, brightness_values: list[float]) -> dict[float, float]:
        ...


class HilbertConverter(GenericCurveConverter):
    def __init__(self, curve_order: int) -> None:
        assert curve_order == 1, "Only order 1 curve (2x2) supported so far"
        super().__init__(curve_order, 2**curve_order, hilbert_curve)

    def assign_frequencies(self, brightness_values: list[float]) -> dict[float, float]:
        base = 440.0
        frequencies = [
            base,
            base * 5 / 4,
            base * 4 / 3,
            base * 3 / 2,
        ]
        return dict(zip(frequencies, brightness_values))


class PeanoConverter(GenericCurveConverter):
    def __init__(self, curve_order: int) -> None:
        assert curve_order == 1, "Only order 1 curve (3x3) supported so far"
        super().__init__(curve_order, 3**curve_order, peano_curve)

    def assign_frequencies(self, brightness_values: list[float]) -> dict[float, float]:
        base = 440.0

        # https://en.wikipedia.org/wiki/Just_intonation
        # fmt: off
        frequencies = [
            base,           # base
            base *  9 / 8,  # second
            base *  5 / 4,  # third
            base *  4 / 3,  # fourth
            base *  3 / 2,  # fifth
            base *  5 / 3,  # sixth
            base * 16 / 9,  # minor seventh
            base * 15 / 8,  # major seventh
            base * 2,       # octave
        ]
        # fmt: on
        return dict(zip(frequencies, brightness_values))


@dataclass
class DivideConverter(Converter):
    def convert_processed_frame(self, frame: Mat) -> dict[float, float]:
        # resize to 1x1, 2x2, 4x4, ... and assign a different frequency to each pixel
        freq_strengths: dict[float, float] = {}

        freqs = [440.0]
        for exp in range(3):
            side_length = 2**exp
            frequency_ratio = 2**4**-exp
            resized_frame = cv2.resize(
                frame, (side_length, side_length), interpolation=cv2.INTER_AREA
            )
            self.display_frame(resized_frame, caption=f"{side_length}x{side_length}")

            curve = hilbert_curve(n=side_length - 1)
            for freq, point in zip(freqs, curve):
                freq_strengths[freq] = resized_frame[point] / 256

            # spread each frequency into 4 by multiplying it by a ratio twice, same with dividing
            freqs = list(
                itertools.chain.from_iterable(
                    [self.spread(f, frequency_ratio) for f in freqs]
                )
            )

        return freq_strengths

    @staticmethod
    def spread(frequency: float, ratio: float) -> list[float]:
        return [
            frequency / ratio**2,
            frequency / ratio,
            frequency * ratio,
            frequency * ratio**2,
        ]
