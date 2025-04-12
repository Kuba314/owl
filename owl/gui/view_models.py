from pathlib import Path
from typing import Any, cast
import logging
import threading
import time

from PyQt6.QtCore import QObject, pyqtBoundSignal, pyqtSignal
import cv2

from owl.converters import BaseConverter
from owl.gui.models import ConverterModel
from owl.output_stream import LiveAudioOutputStream
from owl.types import Frame


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
    new_cam_frame = pyqtSignal(object, name="new_cam_frame")
    new_converter_frame = pyqtSignal(object, name="new_converter_frame")

    def __init__(self, model: ConverterModel):
        super().__init__()
        self._model = model
        self._set_converter(model.construct_converter())
        self._capture = None

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

        self.converter_updated.connect(self._set_converter)

        self._converter_thread = threading.Thread(
            target=self._converter_loop, daemon=True
        )
        self._converter_thread.start()

    @property
    def model(self) -> ConverterModel:
        return self._model

    def set_input_source(self, input_source: Path | int | None) -> None:
        self._model.input_source = input_source

        if self._capture is not None:
            self._capture.release()

        if isinstance(input_source, int):
            self._capture = cv2.VideoCapture(input_source)
        elif isinstance(input_source, Path):
            self._capture = cv2.VideoCapture(str(input_source))
        else:
            self._capture = None

    def _converter_loop(self) -> None:
        output_stream = LiveAudioOutputStream(sample_rate=self._model.sample_rate)
        while True:
            # do nothing if capture is not open
            if self._capture is None or not self._capture.isOpened():
                time.sleep(0.2)
                continue

            output_stream.open()
            fps = self._capture.get(cv2.CAP_PROP_FPS)
            last_frame = time.time() * 1000
            delta = 1000 / fps

            try:
                while True:
                    # wait for next frame
                    while 1000 * time.time() - last_frame < delta:
                        time.sleep(0.01)

                    last_frame += delta

                    success, frame = self._capture.read()
                    if not success:
                        logging.error("couldn't read from capture")
                        break

                    self._converter.update(cast(Frame, frame))
                    audio_samples = self._converter.get_samples(
                        int(delta * self._converter.sample_rate / 1000)
                    )
                    output_stream.write(audio_samples)
            finally:
                output_stream.close()
                if self._model.loop:
                    self.set_input_source(self._model.input_source)
                else:
                    self._capture.release()
                    self._capture = None

    def _set_converter(self, converter: BaseConverter) -> None:
        self._converter = converter

        self._converter.on(
            "new-input-frame", lambda frame: self.new_cam_frame.emit(frame)
        )
        self._converter.on(
            "new-converter-frame", lambda frame: self.new_converter_frame.emit(frame)
        )
