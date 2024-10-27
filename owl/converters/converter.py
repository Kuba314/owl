from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pyee import EventEmitter

from owl.types import Frame, Signal


@dataclass
class BaseConverter(EventEmitter, ABC):
    sample_rate: int = field(default=48000, kw_only=True)

    def __post_init__(self) -> None:
        super().__init__()

    @abstractmethod
    def update(self, frame: Frame) -> None:
        ...

    @abstractmethod
    def get_samples(self, count: int) -> Signal:
        ...
