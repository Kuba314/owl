from typing import Iterator


def peano(n: int) -> Iterator[tuple[int, int]]:
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
