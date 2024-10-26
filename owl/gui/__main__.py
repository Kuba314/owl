import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

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
    app = Application()
    app.exec()
