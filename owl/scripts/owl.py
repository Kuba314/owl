from collections.abc import Callable
import logging
import time

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
    VerticalScanConverter,
)
from owl.converters.static.shifters import ShiftersConverter
from owl.curves import Curve, HilbertCurve, PeanoCurve
from owl.events import handle_events, handler
from owl.frequency_curve import FrequencyCurve
from owl.soundgen import (
    BaseAudioOutputStream,
    Envelope,
    FileAudioOutputStream,
    LiveAudioOutputStream,
    MultiSineGen,
)
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
        default="camera:0",
        help='input source, use "camera:<index>" or "file:<filename>" (default: "camera:0")',
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


@handler("converter:frame:pre")
def handle_converter_frame_pre(frame: Frame) -> None:
    cv2.imshow("Converter frame pre", frame)


@handler("converter:frame:post")
def handle_converter_output(frame: Frame) -> None:
    cv2.imshow("Converter frame post", frame)


@handler("converter:outputs")
def handle_converter_outputs(frames: list[Frame]) -> None:
    for i, frame in enumerate(frames, 1):
        cv2.imshow(f"Converter output {i}", frame)


def init_logging() -> None:
    # edited version of https://stackoverflow.com/a/56944256/8844422
    class ColoredLevelnameFormatter(logging.Formatter):
        COLORS = {
            logging.DEBUG: "\x1b[30m",
            logging.INFO: "\x1b[1;34m",
            logging.WARNING: "\x1b[1;33m",
            logging.ERROR: "\x1b[1;31m",
            logging.CRITICAL: "\x1b[37;41m",
        }

        def format(self, record):
            color = self.COLORS.get(record.levelno)
            fmt = f"{{asctime}} {{name:14}} {color}{{levelname:10}}\033[0m {{message}}"
            formatter = logging.Formatter(fmt, style="{")
            return formatter.format(record)

    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredLevelnameFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logging.basicConfig


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
    sound_cue = envelope.apply(sound_cue, sample_rate)
    return sound_cue


def open_capture(input: str) -> cv2.VideoCapture:
    if ":" not in input:
        raise ValueError('Expected "<method>:<spec>" as input param')

    match input.split(":", 1):
        case "camera", index:
            return cv2.VideoCapture(int(index))
        case "file", filename:
            return cv2.VideoCapture(filename)
        case method, _:
            raise ValueError(f'Invalid input method "{method}"')
        case _:
            assert False, "unreachable"


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
        assert False, "unreachable"


def instantiate_output_stream(
    parsed: Args.shape,
    request_next_samples: Callable[[int], Signal],
) -> BaseAudioOutputStream:
    if parsed.output is not None:
        return FileAudioOutputStream(
            filename=parsed.output,
            next_samples_callback=request_next_samples,
            sample_rate=parsed.sample_rate,
        )
    else:
        return LiveAudioOutputStream(
            next_samples_callback=request_next_samples,
            sample_rate=parsed.sample_rate,
        )


def main_loop(cap: cv2.VideoCapture, converter: BaseConverter) -> None:
    fps = cap.get(cv2.CAP_PROP_FPS)
    last_frame = time.time() * 1000

    while cap.isOpened():
        # wait for next frame
        while 1000 * time.time() - last_frame < 1000 / fps:
            time.sleep(0.01)

        # read frame from capture
        success, frame = cap.read()
        if not success:
            logger.error("Couldn't read from capture")
            break

        last_frame += 1000 / fps
        converter.on_new_frame(frame)
        handle_events()

        key_press = cv2.waitKey(delay=1)
        if key_press == ord("q"):
            break


def main() -> None:
    init_logging()
    parsed = Args.parse()

    cap = open_capture(parsed.input)
    if not cap.isOpened():
        raise Exception("Failed to open cv2 capture")

    converter = instantiate_converter(parsed)
    output_stream = instantiate_output_stream(parsed, converter.get_next_samples)

    output_stream.open()
    try:
        main_loop(cap, converter)
    except KeyboardInterrupt:
        pass
    finally:
        output_stream.close()
        cap.release()
        cv2.destroyAllWindows()
