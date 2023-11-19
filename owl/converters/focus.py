from .base import BaseConverter


class BaseFocusConverter(BaseConverter):
    def __init__(self) -> None:
        self._cursor_position = (0, 0)

    @property
    def cursor_position(self) -> tuple[int, int]:
        return self._cursor_position

    def on_cursor_move(self, position: tuple[int, int]) -> None:
        self._cursor_position = position
