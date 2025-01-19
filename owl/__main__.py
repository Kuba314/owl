import logging
import sys
import time
from typing import cast

from arcparse import arcparser, dict_option, dict_positional, option, subparsers
import cv2
import numpy as np

from owl.audio_scale import AudioScale, BarkScale, MelScale
from owl.converters import (
    BaseConverter,
    CircularScanConverter,
    CurveConverter,
    HorizontalScanConverter,
    ScanConverter,
    ShiftersConverter,
    VerticalScanConverter,
)
from owl.curves import Curve, HilbertCurve, PeanoCurve
from owl.frequency_curve import FrequencyCurve
from owl.logging import init_logging
from owl.output_stream import AudioOutputStream, FileAudioOutputStream, LiveAudioOutputStream
from owl.soundgen import Envelope, MultiSineGen
from owl.types import Frame, Signal


logger = logging.getLogger("owl")


class CurveArgs:
    transient_duration: float = 0.01
    curve_cls: type[Curve] = dict_positional(
        {
            "hilbert": HilbertCurve,
            "peano": PeanoCurve,
        },
    )
    order: int = 1


class ScanArgs:
    scan_conv_cls: type[ScanConverter] = dict_positional(
        {
            "vertical": VerticalScanConverter,
            "horizontal": HorizontalScanConverter,
            "circular": CircularScanConverter,
        },
    )
    strip_count: int = option("-c")
    freqs_per_strip: int = option("-n")
    ms_per_frame: int

    cue: bool


class ShiftersArgs:
    k: int = option(short_only=True)
    intensity_levels: int = 16
    transient_duration: float = 0.01
    curve_cls: type[Curve] = dict_positional(
        {
            "hilbert": HilbertCurve,
            "peano": PeanoCurve,
        },
    )
    order: int = 1


@arcparser
class Args:
    input: str = option(
        "-i",
        default=":0",
        help='input source, use ":<index>" for camera or "<filename>" (default: ":0")',
    )
    output: str | None = option("-o")

    audio_scale_cls: type[AudioScale] = dict_option(
        {
            "mel": MelScale,
            "bark": BarkScale,
        },
        name_override="scale",
        default=MelScale,
    )
    lowest_frequency: float = option("-lo", default=100)
    highest_frequency: float = option("-hi", default=800)
    sample_rate: int = option(default=48000)
    converter: CurveArgs | ScanArgs | ShiftersArgs = subparsers("curve", "scan", "shifters")


def generate_sound_cue(sample_rate: int) -> Signal:
    sound_cue_duration = 0.03
    sound_cue_volume = 0.1
    sound_cue = (
        np.sin(
            np.linspace(
                0,
                2 * np.pi * 1000 * sound_cue_duration,
                int(sample_rate * sound_cue_duration),
            )
        )
        * sound_cue_volume
    )
    envelope = Envelope(0.003, 0.0005, 0.0005, 0.8)
    return envelope.apply(sound_cue, sample_rate)


def open_capture(input: str) -> cv2.VideoCapture:
    if input.startswith(":"):
        return cv2.VideoCapture(int(input[1:]))
    return cv2.VideoCapture(input)


def instantiate_converter(parsed: Args.shape) -> BaseConverter:
    scale = parsed.audio_scale_cls(parsed.lowest_frequency, parsed.highest_frequency)

    if isinstance(curve_args := parsed.converter, CurveArgs):
        curve = curve_args.curve_cls(order=curve_args.order)
        frequencies = scale.get_range(curve.side_length ** 2)
        return CurveConverter(
            frequency_curve=FrequencyCurve(curve, frequencies),
            sine_gen=MultiSineGen(frequencies),
            transient_duration=curve_args.transient_duration,
            sample_rate=parsed.sample_rate,
        )
    elif isinstance(scan_args := parsed.converter, ScanArgs):
        return scan_args.scan_conv_cls(
            strip_count=scan_args.strip_count,
            frequencies=scale.get_range(scan_args.freqs_per_strip),
            ms_per_frame=scan_args.ms_per_frame,
            sound_cue=generate_sound_cue(parsed.sample_rate) if scan_args.cue else None,
            sample_rate=parsed.sample_rate,
        )
    elif isinstance(shifters_args := parsed.converter, ShiftersArgs):
        curve = shifters_args.curve_cls(order=shifters_args.order)
        return ShiftersConverter(
            frequency_curve=FrequencyCurve.from_scale(curve, scale),
            sine_gen=MultiSineGen.blank(count=shifters_args.k),
            intensity_levels=shifters_args.intensity_levels,
            transient_duration=shifters_args.transient_duration,
            sample_rate=parsed.sample_rate,
        )
    else:
        raise AssertionError("unreachable")


def instantiate_output_stream(output_filename: str | None, sample_rate: int) -> AudioOutputStream:
    if output_filename is not None:
        return FileAudioOutputStream(filename=output_filename, sample_rate=sample_rate)
    return LiveAudioOutputStream(sample_rate=sample_rate)


def main_loop(cap: cv2.VideoCapture, converter: BaseConverter, output_stream: AudioOutputStream) -> None:
    fps = cap.get(cv2.CAP_PROP_FPS)
    last_frame = time.time() * 1000

    delta = 1000 / fps
    while cap.isOpened():
        # wait for next frame
        while 1000 * time.time() - last_frame < delta:
            time.sleep(0.01)

        last_frame += delta

        success, frame = cap.read()
        if not success:
            logger.debug("couldn't read from capture, stopping")
            break

        converter.update(cast(Frame, frame))
        audio_samples = converter.get_samples(int(delta * converter.sample_rate / 1000))
        output_stream.write(audio_samples)

        key_press = cv2.waitKey(delay=1)
        if key_press == ord("q"):
            break


def main() -> int:
    init_logging()
    args = Args.parse()

    cap = open_capture(args.input)
    if not cap.isOpened():
        print("error: Failed to open cv2 capture", file=sys.stderr)
        return 1

    output_stream = instantiate_output_stream(args.output, args.sample_rate)
    converter = instantiate_converter(args)

    try:
        output_stream.open()
        main_loop(cap, converter, output_stream)
    except KeyboardInterrupt:
        pass
    finally:
        output_stream.close()
        cap.release()
        cv2.destroyAllWindows()

    return 0
