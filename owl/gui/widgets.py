from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .options_widgets import (
    CommonConverterOptions,
    CurveConverterOptions,
    ScanConverterOptions,
    ShiftersConverterOptions,
)
from .view_models import ConverterViewModel


class SidePanel(QWidget):
    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model

        self._converter_options_widgets = [
            ("curve", CurveConverterOptions(view_model)),
            ("scan", ScanConverterOptions(view_model)),
            ("shifters", ShiftersConverterOptions(view_model)),
        ]

        # initialize common converter options
        self._converter_common_options = CommonConverterOptions(view_model)

        # initialize stack
        self._converter_specific_options_stack = QStackedWidget()
        for _, options_widget in self._converter_options_widgets:
            self._converter_specific_options_stack.addWidget(options_widget)

        # initialize combo box
        self._converter_select = QComboBox()
        for i, (name, _) in enumerate(self._converter_options_widgets):
            self._converter_select.insertItem(i, name)

        # connect and emit select signal
        self._converter_select.currentIndexChanged.connect(
            lambda index: self._converter_specific_options_stack.setCurrentIndex(index)
        )
        self._converter_select.currentIndexChanged.connect(
            lambda index: self._converter_options_widgets[index][1].selected.emit()
        )
        self._converter_select.currentIndexChanged.emit(0)

        layout = QVBoxLayout()
        layout.addWidget(self._converter_select)
        layout.addWidget(self._converter_common_options)
        layout.addWidget(self._converter_specific_options_stack)
        self.setLayout(layout)


class MainGrid(QWidget):
    def __init__(self, view_model: ConverterViewModel):
        super().__init__()

        layout = QGridLayout()
        layout.addWidget(QLabel("main grid 1"), 0, 0)
        layout.addWidget(QLabel("main grid 2"), 0, 1)
        layout.addWidget(QLabel("main grid 3"), 1, 0, 1, 2)

        self.setLayout(layout)


class CentralWidget(QWidget):
    def __init__(self, view_model: ConverterViewModel):
        super().__init__()

        side_panel = SidePanel(view_model)
        side_panel.setMaximumWidth(300)

        layout = QHBoxLayout()
        layout.addWidget(side_panel)
        layout.addWidget(MainGrid(view_model))

        self.setLayout(layout)
