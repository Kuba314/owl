from typing import Any

from PyQt6.QtCore import QObject, pyqtBoundSignal, pyqtSignal

from owl.converters import BaseConverter
from owl.gui.models import ConverterModel


class ConverterViewModel(QObject):
    input_frame_updated = pyqtSignal(object, name="input_frame_updated")
    processed_frame_updated = pyqtSignal(object, name="processed_frame_updated")

    converter_class_updated = pyqtSignal(object, name="converter_class_updated")
    sample_rate_updated = pyqtSignal(int, name="sample_rate_updated")
    audio_scale_class_updated = pyqtSignal(object, name="audio_scale_class_updated")
    lowest_frequency_updated = pyqtSignal(float, name="lowest_frequency_updated")
    highest_frequency_updated = pyqtSignal(float, name="highest_frequency_updated")

    curve_class_updated = pyqtSignal(object, name="curve_class_updated")
    curve_order_updated = pyqtSignal(int, name="curve_order_updated")

    transient_duration_updated = pyqtSignal(float, name="transient_duration_updated")
    strip_count_updated = pyqtSignal(int, name="strip_count_updated")
    freqs_per_strip_updated = pyqtSignal(int, name="freqs_per_strip_updated")
    ms_per_frame_updated = pyqtSignal(int, name="ms_per_frame_updated")

    intensity_levels_updated = pyqtSignal(int, name="intensity_levels_updated")
    point_count_updated = pyqtSignal(int, name="point_count_updated")

    converter_updated = pyqtSignal(BaseConverter, name="converter_updated")

    def __init__(self, model: ConverterModel):
        super().__init__()
        self._model = model

        for name in vars(self.__class__):
            if not name.endswith("_updated") or name == "converter_updated":
                continue

            signal = getattr(self, name)
            if not isinstance(signal, pyqtBoundSignal):
                continue

            name = name[: -len("_updated")]

            def update_value(name: str, value: Any) -> None:
                setattr(self._model, name, value)
                self.converter_updated.emit(self._model.construct_converter())

            signal.connect(lambda value, name=name: update_value(name, value))

        self.converter_updated.connect(lambda converter: print(converter))

    @property
    def model(self) -> ConverterModel:
        return self._model
