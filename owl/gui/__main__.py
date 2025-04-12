import logging
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from owl.logging import init_logging

from .models import ConverterModel
from .view_models import ConverterViewModel
from .widgets import CentralWidget


class Application(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        model = ConverterModel()
        view_model = ConverterViewModel(model)
        view = CentralWidget(view_model)

        self._window = QMainWindow()
        self._window.setCentralWidget(view)
        self._window.resize(1150, 750)
        self._window.show()


def main() -> None:
    init_logging(level=logging.INFO)

    # TODO: underflow should increase latency, possible skip frames if no frames were skipped for some time
    # converter produces frames, audio has callback which wants frames
    # can generate event on underflow, should store a few packets in buffer (purposely not send to cb)
    app = Application()
    sys.exit(app.exec())
