from dataclasses import dataclass
from pathlib import Path

from owl.audio_scale import AudioScale, MelScale
from owl.converters import (
    BaseConverter,
    CurveConverter,
    ScanConverter,
    ShiftersConverter,
)
from owl.curves import Curve, HilbertCurve
from owl.frequency_curve import FrequencyCurve
from owl.soundgen import MultiSineGen
from owl.types import Signal


@dataclass
class ConverterModel:
    converter_class: type[BaseConverter] = CurveConverter
    sample_rate: int = 48000
    audio_scale_class: type[AudioScale] = MelScale
    lowest_frequency: float = 1000
    highest_frequency: float = 8000

    curve_class: type[Curve] = HilbertCurve
    curve_order: int = 2

    sound_cue: Signal | None = None
    transient_duration: float = 0.01
    strip_count: int = 4
    freqs_per_strip: int = 4
    ms_per_frame: int = 500

    intensity_levels: int = 4
    point_count: int = 4

    input_source: Path | int | None = None

    def construct_converter(self) -> BaseConverter:
        audio_scale = self.construct_audio_scale()

        if issubclass(self.converter_class, CurveConverter):
            curve = self.construct_curve()
            frequencies = audio_scale.get_range(curve.side_length**2)
            return CurveConverter(
                frequency_curve=FrequencyCurve(curve, frequencies),
                sine_gen=MultiSineGen(frequencies),
                transient_duration=self.transient_duration,
                sample_rate=self.sample_rate,
            )
        elif issubclass(self.converter_class, ScanConverter):
            return self.converter_class(
                strip_count=self.strip_count,
                frequencies=audio_scale.get_range(self.freqs_per_strip),
                ms_per_frame=self.ms_per_frame,
                sound_cue=self.sound_cue,
                sample_rate=self.sample_rate,
            )
        elif issubclass(self.converter_class, ShiftersConverter):
            curve = self.construct_curve()
            return ShiftersConverter(
                frequency_curve=FrequencyCurve.from_scale(curve, audio_scale),
                sine_gen=MultiSineGen.blank(count=self.point_count),
                intensity_levels=self.intensity_levels,
                transient_duration=self.transient_duration,
                sample_rate=self.sample_rate,
            )
        else:
            raise AssertionError("unreachable")

    def construct_curve(self) -> Curve:
        return self.curve_class(order=self.curve_order)

    def construct_audio_scale(self) -> AudioScale:
        return self.audio_scale_class(self.lowest_frequency, self.highest_frequency)
