from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QPushButton,
)

from owl.audio_scale import BarkScale, MelScale
from owl.converters import (
    CircularScanConverter,
    CurveConverter,
    HorizontalScanConverter,
    ShiftersConverter,
    VerticalScanConverter,
)
from owl.curves import HilbertCurve, PeanoCurve
from owl.gui.view_models import ConverterViewModel


def on_valid_input(line_edit: QLineEdit, callback: Callable[[int | float], None]):
    conv = int if isinstance(line_edit.validator(), QIntValidator) else float
    line_edit.textChanged.connect(
        lambda text: callback(conv(text)) if line_edit.hasAcceptableInput() else ()
    )


class CommonConverterOptions(QWidget):
    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        layout = QVBoxLayout()
        self._view_model = view_model

        def input_video_button_clicked() -> None:
            path, path2 = QFileDialog.getOpenFileName(caption="Select video")
            self._view_model.set_input_source(Path(path))

        self._input_selection_file = QPushButton()
        self._input_selection_file.clicked.connect(input_video_button_clicked)

        self._input_selection_cam_index = QLineEdit()
        self._input_selection_cam_index.setValidator(QIntValidator(0, 7))
        on_valid_input(
            self._input_selection_cam_index,
            lambda value: self._view_model.set_input_source(value),
        )

        self._input_selection_stack = QStackedWidget()
        self._input_selection_stack.addWidget(self._input_selection_file)
        self._input_selection_stack.addWidget(self._input_selection_cam_index)

        self._input_source = QComboBox()
        self._input_source.addItem("file")
        self._input_source.addItem("webcam")
        self._input_source.currentIndexChanged.connect(
            self._input_selection_stack.setCurrentIndex
        )

        layout.addWidget(self._input_source)
        layout.addWidget(self._input_selection_stack)

        self._audio_scale = QComboBox()
        self._audio_scale.addItem("Mel")
        self._audio_scale.addItem("Bark")
        self._audio_scale.currentIndexChanged.connect(
            lambda ix: self._view_model.audio_scale_class_updated.emit(
                MelScale if ix == 0 else BarkScale
            )
        )
        layout.addWidget(QLabel("audio scale"))
        layout.addWidget(self._audio_scale)

        self._lowest_frequency = QLineEdit(str(view_model.model.lowest_frequency))
        self._lowest_frequency.setValidator(QDoubleValidator(30, 20000, 2))
        on_valid_input(
            self._lowest_frequency,
            lambda value: self._view_model.lowest_frequency_updated.emit(value),
        )
        layout.addWidget(QLabel("lowest frequency"))
        layout.addWidget(self._lowest_frequency)

        self._highest_frequency = QLineEdit(str(view_model.model.highest_frequency))
        self._highest_frequency.setValidator(QDoubleValidator(30, 20000, 2))
        on_valid_input(
            self._highest_frequency,
            lambda value: self._view_model.highest_frequency_updated.emit(value),
        )
        layout.addWidget(QLabel("highest frequency"))
        layout.addWidget(self._highest_frequency)

        self.setLayout(layout)


class CurveConverterOptions(QWidget):
    selected = pyqtSignal(name="selected")

    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model
        layout = QVBoxLayout()

        self.selected.connect(
            lambda: self._view_model.converter_class_updated.emit(CurveConverter)
        )

        # curve args
        self._curve_class = QComboBox()
        self._curve_class.addItem("hilbert")
        self._curve_class.addItem("peano")
        self._curve_class.currentIndexChanged.connect(
            lambda ix: self._view_model.curve_class_updated.emit(
                HilbertCurve if ix == 0 else PeanoCurve
            )
        )
        layout.addWidget(QLabel("curve type"))
        layout.addWidget(self._curve_class)

        self._curve_order = QLineEdit(str(view_model.model.curve_order))
        self._curve_order.setValidator(QIntValidator(1, 6))
        on_valid_input(
            self._curve_order,
            lambda value: self._view_model.curve_order_updated.emit(value),
        )
        layout.addWidget(QLabel("curve order"))
        layout.addWidget(self._curve_order)

        self._transient_duration = QLineEdit(str(view_model.model.transient_duration))
        self._transient_duration.setValidator(QDoubleValidator(0.0001, 1.0, 4))
        on_valid_input(
            self._transient_duration,
            lambda value: self._view_model.transient_duration_updated.emit(value),
        )
        layout.addWidget(QLabel("transient duration"))
        layout.addWidget(self._transient_duration)

        layout.addStretch()
        self.setLayout(layout)


class ScanConverterOptions(QWidget):
    selected = pyqtSignal(name="selected")

    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model
        layout = QVBoxLayout()

        self.selected.connect(
            lambda: self._view_model.converter_class_updated.emit(
                scan_converters[self._scan_type.currentIndex()]
            )
        )

        self._scan_type = QComboBox()
        self._scan_type.addItem("vertical")
        self._scan_type.addItem("horizontal")
        self._scan_type.addItem("circular")
        scan_converters = [
            VerticalScanConverter,
            HorizontalScanConverter,
            CircularScanConverter,
        ]
        self._scan_type.currentIndexChanged.connect(
            lambda ix: self._view_model.converter_class_updated.emit(
                scan_converters[ix]
            )
        )
        layout.addWidget(QLabel("scan type"))
        layout.addWidget(self._scan_type)

        self._strip_count = QLineEdit(str(view_model.model.strip_count))
        self._strip_count.setValidator(QIntValidator(1, 6))
        on_valid_input(
            self._strip_count,
            lambda value: self._view_model.strip_count_updated.emit(value),
        )
        layout.addWidget(QLabel("strip count"))
        layout.addWidget(self._strip_count)

        self._transient_duration = QLineEdit(str(view_model.model.transient_duration))
        self._transient_duration.setValidator(QDoubleValidator(0.0001, 1.0, 4))
        on_valid_input(
            self._transient_duration,
            lambda value: self._view_model.transient_duration_updated.emit(value),
        )
        layout.addWidget(QLabel("transient duration"))
        layout.addWidget(self._transient_duration)

        layout.addStretch()
        self.setLayout(layout)


class ShiftersConverterOptions(QWidget):
    selected = pyqtSignal(name="selected")

    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model
        layout = QVBoxLayout()

        self.selected.connect(
            lambda: self._view_model.converter_class_updated.emit(ShiftersConverter)
        )

        self._intensity_levels = QLineEdit(str(view_model.model.intensity_levels))
        self._intensity_levels.setValidator(QIntValidator(2, 32))
        on_valid_input(
            self._intensity_levels,
            lambda value: self._view_model.intensity_levels_updated.emit(value),
        )
        layout.addWidget(QLabel("intensity levels"))
        layout.addWidget(self._intensity_levels)

        self._point_count = QLineEdit(str(view_model.model.point_count))
        self._point_count.setValidator(QIntValidator(2, 32))
        on_valid_input(
            self._point_count,
            lambda value: self._view_model.point_count_updated.emit(value),
        )
        layout.addWidget(QLabel("point count"))
        layout.addWidget(self._point_count)

        # curve args
        self._curve_class = QComboBox()
        self._curve_class.addItem("hilbert")
        self._curve_class.addItem("peano")
        self._curve_class.currentIndexChanged.connect(
            lambda ix: self._view_model.curve_class_updated.emit(
                HilbertCurve if ix == 0 else PeanoCurve
            )
        )
        layout.addWidget(QLabel("curve type"))
        layout.addWidget(self._curve_class)

        self._curve_order = QLineEdit(str(view_model.model.curve_order))
        self._curve_order.setValidator(QIntValidator(1, 6))
        on_valid_input(
            self._curve_order,
            lambda value: self._view_model.curve_order_updated.emit(value),
        )
        layout.addWidget(QLabel("curve order"))
        layout.addWidget(self._curve_order)

        layout.addStretch()
        self.setLayout(layout)
