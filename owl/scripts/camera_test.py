import cv2

from owl.converter import Converter, HilbertConverter, DivideConverter
from owl.synthesizer import Synthesizer


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Capture didn't open")

    converter: Converter
    converter = DivideConverter()
    # converter = HilbertConverter(curve_order=1)
    synth = Synthesizer(rate=48000)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Couldn't read from capture")

        freqs = converter.convert(cv2.flip(frame, 1))

        key_press = cv2.waitKey(1)
        if key_press == ord("q"):
            break
        if key_press == ord("p"):
            print(freqs)
            signal = synth.synthesize(freqs, 1)
            synth.play(signal)

    cap.release()
    cv2.destroyAllWindows()
