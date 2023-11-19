from abc import abstractmethod

from dataclasses import dataclass, field

from owl.soundgen import MultiFreqGen
from owl.types import Signal, Frame
from ..base import BaseConverter


@dataclass
class ConstFreqConverter(BaseConverter):
    frequencies: list[float]

    _cursor_position: tuple[int, int] = field(default=(0, 0), init=False)

    def __post_init__(self) -> None:
        super().__post_init__()

        self._sound_gen = MultiFreqGen(freqs=self.frequencies)

    def register_audio_callback(self) -> None:
        self._audio_stream.open()

    def unregister_audio_callback(self) -> None:
        self._audio_stream.close()

    def on_new_frame(self, frame: Frame) -> None:
        volumes = self._extract_volumes(frame)
        assert len(volumes) == len(self._sound_gen.freqs)
        self._sound_gen.set_volumes(volumes, backoff=0.01)

    def get_next_samples(self, count: int) -> Signal:
        return self._sound_gen.get_next_samples(count)

    def on_cursor_move(self, position: tuple[int, int]) -> None:
        self._cursor_position = position

    @abstractmethod
    def _extract_volumes(self, frame: Frame) -> list[float]:
        ...
