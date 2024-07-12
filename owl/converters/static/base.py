from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from owl.soundgen import MultiSineGen
from owl.types import Frame, Signal

from ..converter import BaseConverter


@dataclass
class Sine:
    frequency: float
    volume: float


@dataclass
class SineConverter(BaseConverter):
    sine_gen: MultiSineGen
    transient_duration: float

    _first_frame: bool = field(init=False, default=True)

    @property
    def sine_count(self) -> int:
        return len(self.sine_gen.freqs)

    def update(self, frame: Frame) -> None:
        sines = self._extract_sines(frame)
        assert len(sines) == len(self.sine_gen.freqs)

        transient_duration = 0 if self._first_frame else self.transient_duration
        self._first_frame = False
        self.sine_gen.set_frequencies((sine.frequency for sine in sines), transient_duration=transient_duration)
        self.sine_gen.set_volumes((sine.volume for sine in sines), transient_duration=transient_duration)

    def get_samples(self, count: int) -> Signal:
        return self.sine_gen.get_next_samples(count)

    @abstractmethod
    def _extract_sines(self, frame: Frame) -> Sequence[Sine]:
        ...
