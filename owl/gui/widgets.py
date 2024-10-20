from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class SidePanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("side panel 1"))
        layout.addWidget(QLabel("side panel 2"))
        layout.addWidget(QLabel("side panel 3"))

        self.setLayout(layout)


class MainGrid(QWidget):
    def __init__(self):
        super().__init__()

        layout = QGridLayout()
        layout.addWidget(QLabel("main grid 1"), 0, 0)
        layout.addWidget(QLabel("main grid 2"), 0, 1)
        layout.addWidget(QLabel("main grid 3"), 1, 0)
        layout.addWidget(QLabel("main grid 4"), 1, 1)

        self.setLayout(layout)


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        layout.addWidget(SidePanel())
        layout.addWidget(MainGrid())

        self.setLayout(layout)
