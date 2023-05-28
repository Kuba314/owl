from typing import Iterator, Callable, TypeAlias, cast

from hilbertcurve.hilbertcurve import HilbertCurve

CurveGenerator: TypeAlias = Callable[[int], Iterator[tuple[int, int]]]


def peano_curve(n: int) -> Iterator[tuple[int, int]]:
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

    yield from _peano(n, 0, 0)


def hilbert_curve(n: int) -> Iterator[tuple[int, int]]:
    if n == 0:
        yield (0, 0)
        return

    curve = HilbertCurve(p=n, n=2)
    for i in range(4**n):
        yield cast(tuple[int, int], tuple(curve.point_from_distance(i)))
