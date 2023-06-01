import cv2
from argparse import ArgumentParser, Namespace

from owl.converter import Converter, HilbertConverter, DivideConverter, PeanoConverter
from owl.scripts.soundgen_test import Soundgen


converters: dict[str, Converter] = {
    "divide": DivideConverter(),
    "hilbert": HilbertConverter(curve_order=1),
    "peano": PeanoConverter(curve_order=1),
}


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--converter", choices=list(converters.keys()), required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Capture didn't open")

    freqs = [
        440,
        440 * 3 / 2,
        440 * 5 / 4,
        440 * 16 / 9,
    ]

    converter = converters[args.converter]
    soundgen = Soundgen(freqs=freqs)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Couldn't read from capture")

        freq_volumes = converter.convert(cv2.flip(frame, 1))
        soundgen.set_volumes(freq_volumes.values(), backoff=0.01)

        key_press = cv2.waitKey(1)
        if key_press == ord("q"):
            break
        # if key_press == ord("p"):
        #     print(freqs)
        #     signal = synth.synthesize(freqs, 1)
        #     synth.play(signal)

    cap.release()
    cv2.destroyAllWindows()
