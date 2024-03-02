

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Self

from owl.audio_scale import AudioScale
from owl.curves import Curve


@dataclass(frozen=True)
class FrequencyCurve:
    curve: Curve
    frequencies: Sequence[float]

    @property
    def side_length(self) -> int:
        return self.curve.side_length

    def get_frequency(self, position: tuple[int, int]) -> float | None:
        if (ix := self.curve.index_of(position)) is not None:
            return self.frequencies[ix]
        return None

    def __iter__(self) -> Iterator[tuple[tuple[int, int], float]]:
        yield from zip(self.curve.generate(), self.frequencies)

    @classmethod
    def from_scale(cls, curve: Curve, audio_scale: AudioScale) -> Self:
        return cls(
            curve=curve,
            frequencies=audio_scale.get_range(curve.side_length ** 2),
        )
