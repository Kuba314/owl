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
from owl.curves import Curve, HilbertCurve, PeanoCurve
from owl.events import handle_events, handler
from owl.soundgen import Envelope
from owl.types import Frame, Signal


logger = logging.getLogger("owl")


class CurveArgs:
    curve_cls: type[Curve] = dict_positional(
        {
            "hilbert": HilbertCurve,
            "peano": PeanoCurve,
        },
        name_override="curve",
    )
    order: int = 1


class ScanArgs:
    scan_conv_cls: type[ScanConverter] = dict_positional(
        {
            "vertical": VerticalScanConverter,
            "horizontal": HorizontalScanConverter,
            "circular": CircularScanConverter,
        },
        name_override="scan_type",
    )
    strip_count: int = option("-c")
    freqs_per_strip: int = option("-n")
    ms_per_frame: int

    cue: bool


@arcparser
class Args:
    input_type: str = option(default="camera", choices=["camera", "file"])
    input_spec: str = option(default="0")
    # output: Literal["window", "audio", "video"] = option("-o")

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
    converter: CurveArgs | ScanArgs = subparsers("curve", "scan")


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


def open_capture(input_type: str, input_spec: str) -> cv2.VideoCapture:
    if input_type == "camera":
        return cv2.VideoCapture(int(input_spec))
    elif input_type == "file":
        return cv2.VideoCapture(input_spec)
    else:
        assert False, "unreachable"


def instantiate_converter(parsed: Args.shape) -> BaseConverter:
    scale = parsed.audio_scale_cls(parsed.lowest_frequency, parsed.highest_frequency)

    if isinstance(curve_args := parsed.converter, CurveArgs):
        curve = curve_args.curve_cls(order=curve_args.order)
        return CurveConverter(
            frequencies=scale.get_range(curve.side_length**2),
            curve=curve,
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
    else:
        assert False, "unreachable"


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


def main() -> None:
    init_logging()
    parsed = Args.parse()

    cap = open_capture(parsed.input_type, parsed.input_spec)
    if not cap.isOpened():
        raise Exception("Failed to open cv2 capture")

    converter = instantiate_converter(parsed)
    converter.start()

    fps = cap.get(cv2.CAP_PROP_FPS)
    last_frame = time.time() * 1000
    try:
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
    except KeyboardInterrupt:
        pass
    finally:
        converter.stop()
        cap.release()
        cv2.destroyAllWindows()
