import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from .widgets import CentralWidget


class Application(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        self._window = QMainWindow()
        self._window.setCentralWidget(CentralWidget())
        self._window.show()


def main() -> None:
    app = Application()
    app.exec()
