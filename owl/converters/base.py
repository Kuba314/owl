from abc import ABC, abstractmethod

from dataclasses import dataclass, field

from owl.soundgen import AudioOutputStream
from owl.types import Frame, Signal


@dataclass
class BaseConverter(ABC):
    sample_rate: int = field(default=48000, kw_only=True)

    def __post_init__(self) -> None:
        self._audio_stream = AudioOutputStream(
            next_samples_callback=self.get_next_samples,
            sample_rate=self.sample_rate,
        )

    def start(self) -> None:
        self._audio_stream.open()

    def stop(self) -> None:
        self._audio_stream.close()

    @abstractmethod
    def on_new_frame(self, frame: Frame) -> None:
        ...

    @abstractmethod
    def get_next_samples(self, count: int) -> Signal:
        ...
