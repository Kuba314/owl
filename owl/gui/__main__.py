import sys

from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


class Application(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        # side panel
        side_panel = QVBoxLayout()
        side_panel.addWidget(QLabel("side panel 1"))
        side_panel.addWidget(QLabel("side panel 2"))
        side_panel.addWidget(QLabel("side panel 3"))

        # main grid
        main_grid = QGridLayout()
        main_grid.addWidget(QLabel("main grid 1"), 0, 0)
        main_grid.addWidget(QLabel("main grid 2"), 0, 1)
        main_grid.addWidget(QLabel("main grid 3"), 1, 0)
        main_grid.addWidget(QLabel("main grid 4"), 1, 1)

        main_layout = QHBoxLayout()
        main_layout.addLayout(side_panel)
        main_layout.addLayout(main_grid)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        self._window = QMainWindow()
        self._window.setCentralWidget(main_widget)
        self._window.setLayout(main_layout)
        self._window.show()


def main() -> None:
    app = Application()
    app.exec()
