from argparse import ArgumentParser, Namespace
import logging

import cv2
import numpy as np

from owl.audio_scale import BarkScale, MelScale
from owl.converters import (
    CurveConverter,
    HorizontalScanConverter,
    CircularScanConverter,
)
from owl.curves import Curve, HilbertCurve, PeanoCurve
from owl.events import handle_events, handler
from owl.soundgen import Envelope
from owl.types import Frame

logger = logging.getLogger("camera_test")


curves_classes: dict[str, type[Curve]] = {
    "hilbert": HilbertCurve,
    "peano": PeanoCurve,
}


@handler("converter:output")
def handle_converter_output(frame: Frame) -> None:
    cv2.imshow("Converter output", frame)


@handler("converter:outputs")
def handle_converter_outputs(frames: list[Frame]) -> None:
    for i, frame in enumerate(frames, 1):
        cv2.imshow(f"Converter output {i}", frame)


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--curve", choices=list(curves_classes.keys()), required=True)
    parser.add_argument("--curve-order", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    # args = parse_args()

    # open webcam capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Capture didn't open")

    # instantiate converter
    # curve_cls = curves_classes[args.curve]
    # curve = curve_cls(order=args.curve_order)
    scale = MelScale(100, 800)
    # frequencies = scale.get_range(curve.side_length**2)
    sound_cue_duration = 0.01
    sound_cue_volume = 0.1
    sound_cue = (
        np.sin(
            np.linspace(
                0,
                2 * np.pi * 1000 * sound_cue_duration,
                int(48000 * sound_cue_duration),
            )
        )
        * sound_cue_volume
    )
    # envelope = Envelope(0.015, 0.001, 0.001, 0.8)
    # sound_cue = envelope.apply(sound_cue, 48000)
    # signal = np.sin(np.linspace(0, 2 * np.pi, int(48000 / 1000)))
    converter = CircularScanConverter(
        strip_count=4,
        frequencies=scale.get_range(8),
        ms_per_frame=1000,
        ms_between_new_frames=1000 / 10 + 50,
    )
    # converter = HorizontalScanConverter(
    #     ms_per_frame=1000,
    #     strip_count=8,
    #     frequencies=scale.get_range(8),
    #     sound_cue=sound_cue,
    # )

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
