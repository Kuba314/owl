from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from owl.soundgen import MultiSineGen
from owl.types import Frame, Signal

from ..base import BaseConverter


class SineConverter(BaseConverter):
    def __init__(self, initial_frequencies: Sequence[float]):
        self.frequencies = tuple(initial_frequencies)
        self._sound_gen = MultiSineGen(freqs=self.frequencies)

    def on_new_frame(self, frame: Frame) -> None:
        volumes = self._extract_volumes(frame)
        assert len(volumes) == len(self._sound_gen.freqs)
        self._sound_gen.set_volumes(volumes, backoff=0.01)

    def get_next_samples(self, count: int) -> Signal:
        return self._sound_gen.get_next_samples(count)

    @abstractmethod
    def _extract_volumes(self, frame: Frame) -> list[float]:
        ...
