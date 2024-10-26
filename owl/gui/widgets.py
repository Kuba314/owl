from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QResizeEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
)

from .options_widgets import (
    CommonConverterOptions,
    CurveConverterOptions,
    ScanConverterOptions,
    ShiftersConverterOptions,
)
from .view_models import ConverterViewModel

FOREGROUND_COLOR = "#faa"
BACKGROUND_COLOR = "#050"


class SidePanel(QFrame):
    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setLineWidth(3)

        self.setStyleSheet(f"background-color: {FOREGROUND_COLOR}")

        self._converter_options_widgets = [
            ("curve", CurveConverterOptions(view_model)),
            ("scan", ScanConverterOptions(view_model)),
            ("shifters", ShiftersConverterOptions(view_model)),
        ]

        # initialize common converter options
        self._converter_common_options = CommonConverterOptions(view_model)
        self._converter_common_options.setStyleSheet(
            f"background-color: {FOREGROUND_COLOR}"
        )

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


class MaxContentPixmapLabel(QLabel):
    def __init__(self, pixmap: QPixmap, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pixmap = pixmap
        self.setPixmap(pixmap)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event: QResizeEvent) -> None:
        new_pixmap = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(new_pixmap)
        return super().resizeEvent(event)


class MainGrid(QFrame):
    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self.setStyleSheet(f"background-color: {FOREGROUND_COLOR}")
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setLineWidth(3)

        layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        output_layout = QHBoxLayout()
        layout.addLayout(input_layout)
        layout.addLayout(output_layout)

        cam_pixmap = QPixmap.fromImage(QImage("image.png"))
        cam_view = MaxContentPixmapLabel(cam_pixmap)
        converter_view = MaxContentPixmapLabel(cam_pixmap)
        input_layout.addWidget(cam_view)
        input_layout.addWidget(converter_view)

        spectrogram = QLabel("spectrogram")
        spectrogram.setStyleSheet("border: 1px solid red")
        output_layout.addWidget(spectrogram)

        self.setLayout(layout)


class CentralWidget(QSplitter):
    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR}")
        self.setHandleWidth(15)

        side_panel = SidePanel(view_model)
        side_panel.setMinimumWidth(150)
        side_panel.setMaximumWidth(400)

        self.addWidget(side_panel)
        self.addWidget(MainGrid(view_model))
