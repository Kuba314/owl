from collections.abc import Callable
from typing import Any
import logging


_listeners: dict[str, list[Callable[[Any], None]]] = {}


def handler(event: str) -> Callable[[Callable[[Any], None]], Callable[[Any], None]]:
    def decorator_(f: Callable[[Any], None]) -> Callable[[Any], None]:
        _listeners.setdefault(event, []).append(f)
        return f

    return decorator_


def signal(event: str, data: Any) -> None:
    if event not in _listeners:
        logging.warning(f'Event "{event}" sent but no listener for it is registered')
        return

    for listener in _listeners[event]:
        listener(data)


_event_queue: list[tuple[str, Any]] = []


def notify(event: str, data: Any) -> None:
    _event_queue.append((event, data))


def handle_events() -> None:
    while _event_queue:
        event, data = _event_queue.pop()
        signal(event, data)
