from collections.abc import Callable
from pathlib import Path
import re

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QWidget,
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


def on_valid_int_input(line_edit: QLineEdit, callback: Callable[[int], None], min: int | None = None):
    def is_valid_input(text: str) -> int | None:
        if not text.isnumeric():
            return None
        value = int(text)
        if min is not None and value < min:
            return None
        return value

    line_edit.textChanged.connect(
        lambda text: callback(v) if (v := is_valid_input(text)) is not None else ()
    )

def on_valid_float_input(line_edit: QLineEdit, callback: Callable[[float], None]):
    def is_valid_input(text: str) -> float | None:
        if re.match(r"^\d+(\.\d+)?", text):
            return float(text)
        return None

    line_edit.textChanged.connect(
        lambda text: callback(v) if (v := is_valid_input(text)) is not None else ()
    )


class OptionsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._layout = QGridLayout()
        self._row = 0
        self.setLayout(self._layout)

    def add_entry(self, left: QWidget, right: QWidget) -> None:
        self._layout.addWidget(left, self._row, 0)
        self._layout.addWidget(right, self._row, 1)
        self._row += 1

    def add_option(self, name: str, widget: QWidget) -> None:
        self.add_entry(QLabel(name), widget)


class CommonConverterOptions(OptionsWidget):
    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model

        def input_video_button_clicked() -> None:
            path, path2 = QFileDialog.getOpenFileName(caption="Select video")
            self._view_model.set_input_source(Path(path))

        self._input_selection_file = QPushButton()
        self._input_selection_file.setText("Open video")
        self._input_selection_file.clicked.connect(input_video_button_clicked)

        self._input_selection_cam_index = QLineEdit()
        on_valid_int_input(
            self._input_selection_cam_index,
            lambda value: self._view_model.set_input_source(value),
            min=0,
        )

        self._input_selection_stack = QStackedWidget()
        self._input_selection_stack.addWidget(self._input_selection_file)
        self._input_selection_stack.addWidget(self._input_selection_cam_index)
        self._input_selection_stack.setMaximumHeight(40)

        self._input_source = QComboBox()
        self._input_source.addItem("file")
        self._input_source.addItem("webcam")
        self._input_source.currentIndexChanged.connect(
            self._input_selection_stack.setCurrentIndex
        )

        self._layout.addWidget(self._input_source, 0, 0)
        self._layout.addWidget(self._input_selection_stack, 0, 1)
        self._row += 1

        self._audio_scale = QComboBox()
        self._audio_scale.addItem("Mel")
        self._audio_scale.addItem("Bark")
        self._audio_scale.currentIndexChanged.connect(
            lambda ix: self._view_model.audio_scale_class_updated.emit(
                MelScale if ix == 0 else BarkScale
            )
        )

        self.add_option("audio scale", self._audio_scale)

        self._lowest_frequency = QLineEdit(str(view_model.model.lowest_frequency))
        on_valid_int_input(
            self._lowest_frequency,
            lambda value: self._view_model.lowest_frequency_updated.emit(value),
            min=1,
        )
        self.add_option("lowest frequency", self._lowest_frequency)

        self._highest_frequency = QLineEdit(str(view_model.model.highest_frequency))
        on_valid_int_input(
            self._highest_frequency,
            lambda value: self._view_model.highest_frequency_updated.emit(value),
            min=1,
        )
        self.add_option("highest frequency", self._highest_frequency)


class CurveConverterOptions(OptionsWidget):
    selected = pyqtSignal(name="selected")

    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model

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
        self.add_option("curve type", self._curve_class)

        self._curve_order = QLineEdit(str(view_model.model.curve_order))
        on_valid_int_input(
            self._curve_order,
            lambda value: self._view_model.curve_order_updated.emit(value),
        )
        self.add_option("curve order", self._curve_order)

        self._transient_duration = QLineEdit(str(view_model.model.transient_duration))
        on_valid_float_input(
            self._transient_duration,
            lambda value: self._view_model.transient_duration_updated.emit(value),
        )
        self.add_option("transient duration", self._transient_duration)


class ScanConverterOptions(OptionsWidget):
    selected = pyqtSignal(name="selected")

    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model

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
        self.add_option("scan type", self._scan_type)

        self._strip_count = QLineEdit(str(view_model.model.strip_count))
        on_valid_int_input(
            self._strip_count,
            lambda value: self._view_model.strip_count_updated.emit(value),
            min=1,
        )
        self.add_option("strip count", self._strip_count)

        self._freqs_per_strip = QLineEdit(str(view_model.model.freqs_per_strip))
        on_valid_int_input(
            self._freqs_per_strip,
            lambda value: self._view_model.freqs_per_strip_updated.emit(value),
            min=1,
        )
        self.add_option("freqs per strip", self._freqs_per_strip)

        self._ms_per_frame = QLineEdit(str(view_model.model.ms_per_frame))
        on_valid_int_input(
            self._ms_per_frame,
            lambda value: self._view_model.ms_per_frame_updated.emit(value),
            min=1,
        )
        self.add_option("ms per frame", self._ms_per_frame)

        self._transient_duration = QLineEdit(str(view_model.model.transient_duration))
        on_valid_int_input(
            self._transient_duration,
            lambda value: self._view_model.transient_duration_updated.emit(value),
        )
        self.add_option("transient duration", self._transient_duration)


class ShiftersConverterOptions(OptionsWidget):
    selected = pyqtSignal(name="selected")

    def __init__(self, view_model: ConverterViewModel):
        super().__init__()
        self._view_model = view_model

        self.selected.connect(
            lambda: self._view_model.converter_class_updated.emit(ShiftersConverter)
        )

        self._intensity_levels = QLineEdit(str(view_model.model.intensity_levels))
        on_valid_int_input(
            self._intensity_levels,
            lambda value: self._view_model.intensity_levels_updated.emit(value),
            min=1,
        )
        self.add_option("intensity levels", self._intensity_levels)

        self._point_count = QLineEdit(str(view_model.model.point_count))
        on_valid_int_input(
            self._point_count,
            lambda value: self._view_model.point_count_updated.emit(value),
            min=1,
        )
        self.add_option("point count", self._point_count)

        # curve args
        self._curve_class = QComboBox()
        self._curve_class.addItem("hilbert")
        self._curve_class.addItem("peano")
        self._curve_class.currentIndexChanged.connect(
            lambda ix: self._view_model.curve_class_updated.emit(
                HilbertCurve if ix == 0 else PeanoCurve
            )
        )
        self.add_option("curve type", self._curve_class)

        self._curve_order = QLineEdit(str(view_model.model.curve_order))
        on_valid_int_input(
            self._curve_order,
            lambda value: self._view_model.curve_order_updated.emit(value),
        )
        self.add_option("curve order", self._curve_order)
