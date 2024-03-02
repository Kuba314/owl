from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, cast

from hilbertcurve.hilbertcurve import HilbertCurve as HilbertCurveImpl


@dataclass
class Curve(ABC):
    order: int

    @property
    @abstractmethod
    def side_length(self) -> int:
        ...

    @abstractmethod
    def generate(self) -> Iterator[tuple[int, int]]:
        ...

    def index_of(self, pos: tuple[int, int]) -> int | None:
        for i, cpos in enumerate(self.generate()):
            if pos == cpos:
                return i
        return None


class PeanoCurve(Curve):
    @property
    def side_length(self) -> int:
        return 3**self.order

    def generate(self) -> Iterator[tuple[int, int]]:
        x = y = 0
        x_dir = y_dir = 1

        def _peano(depth: int, dx: int, dy: int) -> Iterator[tuple[int, int]]:
            nonlocal x, y, x_dir, y_dir

            if depth == 0:
                yield (x, y)
                x += dx
                y += dy
                return

            yield from _peano(depth - 1, 0, y_dir)
            x_dir = -x_dir
            yield from _peano(depth - 1, 0, y_dir)
            x_dir = -x_dir
            yield from _peano(depth - 1, x_dir, 0)
            y_dir = -y_dir

            yield from _peano(depth - 1, 0, y_dir)
            x_dir = -x_dir
            yield from _peano(depth - 1, 0, y_dir)
            x_dir = -x_dir
            yield from _peano(depth - 1, x_dir, 0)
            y_dir = -y_dir

            yield from _peano(depth - 1, 0, y_dir)
            x_dir = -x_dir
            yield from _peano(depth - 1, 0, y_dir)
            x_dir = -x_dir
            yield from _peano(depth - 1, dx, dy)

        yield from _peano(self.order, 0, 0)


@dataclass
class HilbertCurve(Curve):
    def __post_init__(self) -> None:
        self._curve_impl = HilbertCurveImpl(p=self.order, n=2)

    @property
    def side_length(self) -> int:
        return 2**self.order

    def generate(self) -> Iterator[tuple[int, int]]:
        if self.order == 0:
            yield (0, 0)
            return

        for i in range(4**self.order):
            yield cast(tuple[int, int], tuple(self._curve_impl.point_from_distance(i)))

    def index_of(self, pos: tuple[int, int]) -> int:
        return self._curve_impl.distance_from_point(pos)
