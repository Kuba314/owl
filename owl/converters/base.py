from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from owl.types import Frame, Signal


@dataclass
class BaseConverter(ABC):
    sample_rate: int = field(default=48000, kw_only=True)

    @abstractmethod
    def on_new_frame(self, frame: Frame) -> None:
        ...

    @abstractmethod
    def get_next_samples(self, count: int) -> Signal:
        ...
