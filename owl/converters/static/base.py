from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from owl.soundgen import MultiSineGen
from owl.types import Frame, Signal

from ..base import BaseConverter


@dataclass
class Sine:
    frequency: float
    volume: float


@dataclass
class SineConverter(BaseConverter):
    sine_count: int

    def __post_init__(self):
        self._sound_gen = MultiSineGen(freqs=[200 for _ in range(self.sine_count)])

    def on_new_frame(self, frame: Frame) -> None:
        sines = self._extract_sines(frame)
        assert len(sines) == self.sine_count
        self._sound_gen.set_frequencies((sine.frequency for sine in sines), backoff=0.01)
        self._sound_gen.set_volumes((sine.volume for sine in sines), backoff=0.01)

    def get_next_samples(self, count: int) -> Signal:
        return self._sound_gen.get_next_samples(count)

    @abstractmethod
    def _extract_sines(self, frame: Frame) -> Sequence[Sine]:
        ...
