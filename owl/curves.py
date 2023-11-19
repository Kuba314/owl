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


class HilbertCurve(Curve):
    @property
    def side_length(self) -> int:
        return 2**self.order

    def generate(self) -> Iterator[tuple[int, int]]:
        if self.order == 0:
            yield (0, 0)
            return

        curve = HilbertCurveImpl(p=self.order, n=2)
        for i in range(4**self.order):
            yield cast(tuple[int, int], tuple(curve.point_from_distance(i)))
