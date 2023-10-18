from abc import ABC, abstractmethod
from dataclasses import dataclass
import math

import numpy as np


@dataclass
class AudioScale(ABC):
    min_hz: float
    max_hz: float

    def __post_init__(self) -> None:
        self._min = self.to_scale(self.min_hz)
        self._max = self.to_scale(self.max_hz)

    def get_range(self, count: int) -> np.ndarray:
        return np.array(list(map(self.to_hz, np.linspace(self._min, self._max, count))))

    @abstractmethod
    def to_scale(self, value: float) -> float:
        ...

    @abstractmethod
    def to_hz(self, value: float) -> float:
        ...


class MelScale(AudioScale):
    def to_scale(self, value: float) -> float:
        # https://en.wikipedia.org/wiki/Mel_scale#Formula
        return 2595 * math.log(1 + value / 700)

    def to_hz(self, value: float) -> float:
        return (10 ** (value / 2595) - 1) * 700


class BarkScale(AudioScale):
    def to_scale(self, value: float) -> float:
        # https://en.wikipedia.org/wiki/Bark_scale#Conversions
        return 13 * math.atan(0.00076 * value) + 3.5 * math.atan((value / 7500) ** 2)

    def to_hz(self, value: float) -> float:
        return (10 ** (value / 2595) - 1) * 700
