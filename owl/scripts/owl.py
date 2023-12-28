import logging

import cv2
import numpy as np
from arcparse import arcparser, positional, option, subparsers

from owl.audio_scale import AudioScale, BarkScale, MelScale
from owl.converters import (
    CurveConverter,
    HorizontalScanConverter,
    CircularScanConverter,
    BaseConverter,
    VerticalScanConverter,
    ScanConverter,
)
from owl.curves import Curve, HilbertCurve, PeanoCurve
from owl.events import handle_events, handler
from owl.soundgen import Envelope
from owl.types import Frame

logger = logging.getLogger("camera_test")


def curve_cls(arg: str) -> type[Curve]:
    return {
        "hilbert": HilbertCurve,
        "peano": PeanoCurve,
    }[arg]


class CurveArgs:
    curve_cls: type[Curve] = positional(name_override="curve", converter=curve_cls)
    order: int = 1


def scan_conv_cls(arg: str) -> type[ScanConverter]:
    return {
        "vertical": VerticalScanConverter,
        "horizontal": HorizontalScanConverter,
        "circular": CircularScanConverter,
    }[arg]


class ScanArgs:
    scan_conv_cls: type[ScanConverter] = positional(
        name_override="scan_type", converter=scan_conv_cls
    )
    strip_count: int = option("-c")
    freqs_per_strip: int = option("-n")
    ms_per_frame: int


def audio_scale_cls(arg: str) -> type[AudioScale]:
    return {
        "mel": MelScale,
        "bark": BarkScale,
    }[arg]


@arcparser
class Args:
    # input: str = option("-i")
    # output: Literal["window", "audio", "video"] = option("-o")

    audio_scale_cls: type[AudioScale] = option(
        name_override="scale", converter=audio_scale_cls, default=MelScale
    )
    lowest_frequency: float = option("-lo", default=100)
    highest_frequency: float = option("-hi", default=800)
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


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    parsed = Args.parse()

    # open webcam capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Capture didn't open")

    scale = parsed.audio_scale_cls(parsed.lowest_frequency, parsed.highest_frequency)

    converter: BaseConverter
    if isinstance(curve_args := parsed.converter, CurveArgs):
        curve = curve_args.curve_cls(order=curve_args.order)
        converter = CurveConverter(
            frequencies=scale.get_range(curve.side_length**2),
            curve=curve,
        )
    elif isinstance(scan_args := parsed.converter, ScanArgs):
        converter = scan_args.scan_conv_cls(
            strip_count=scan_args.strip_count,
            frequencies=scale.get_range(scan_args.freqs_per_strip),
            ms_per_frame=scan_args.ms_per_frame,
        )
    else:
        assert False, "unreachable"

    # sound_cue_duration = 0.01
    # sound_cue_volume = 0.1
    # sound_cue = (
    #     np.sin(
    #         np.linspace(
    #             0,
    #             2 * np.pi * 1000 * sound_cue_duration,
    #             int(48000 * sound_cue_duration),
    #         )
    #     )
    #     * sound_cue_volume
    # )
    # envelope = Envelope(0.015, 0.001, 0.001, 0.8)
    # sound_cue = envelope.apply(sound_cue, 48000)
    # signal = np.sin(np.linspace(0, 2 * np.pi, int(48000 / 1000)))
    logger.info("Registering callback")
    converter.start()

    # main loop
    try:
        while True:
            # read frame from webcam capture
            try:
                ret, frame = cap.read()
            except KeyboardInterrupt:
                break
            if not ret:
                logger.error("Couldn't read from capture")

            # pass frame to converter
            converter.on_new_frame(frame)
            handle_events()

            key_press = cv2.waitKey(1)
            if key_press == ord("q"):
                break
    finally:
        converter.stop()
        cap.release()
        cv2.destroyAllWindows()
