from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class CurveConverterOptions(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("curve option 1"))
        layout.addWidget(QLabel("curve option 2"))
        self.setLayout(layout)


class DynamicConverterOptions(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("dynamic option 1"))
        layout.addWidget(QLabel("dynamic option 2"))
        self.setLayout(layout)


class SidePanel(QWidget):
    def __init__(self):
        super().__init__()

        self._converter_options_widgets = [
            ("curve", CurveConverterOptions()),
            ("dynamic", DynamicConverterOptions()),
        ]

        # initialize stack
        self._options_stack = QStackedWidget()
        for _, options_widget in self._converter_options_widgets:
            self._options_stack.addWidget(options_widget)

        # initialize combo box
        self._converter_select = QComboBox()
        for i, (name, _) in enumerate(self._converter_options_widgets):
            self._converter_select.insertItem(i, name)

        # connect and emit select signal
        self._converter_select.currentIndexChanged.connect(
            lambda index: self._options_stack.setCurrentIndex(index)
        )
        self._converter_select.currentIndexChanged.emit(0)

        layout = QVBoxLayout()
        layout.addWidget(self._converter_select)
        layout.addWidget(self._options_stack)
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
