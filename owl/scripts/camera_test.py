import time

import cv2
import numpy as np

from owl.converter import Converter
from owl.synthesizer import Synthesizer


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Capture didn't open")

    converter = Converter(side_length=2)
    synth = Synthesizer(rate=48000)

    start = time.time()
    fps = 0
    while True:
        if (now := time.time()) - start >= 1:
            print(f"fps: {fps}")
            start = now
            fps = 1
        else:
            fps += 1

        ret, frame = cap.read()
        if not ret:
            print("Couldn't read from capture")

        strip = converter.convert(frame)
        cv2.imshow("frame", strip)

        key_press = cv2.waitKey(1)
        if key_press == ord("q"):
            break
        if key_press == ord("p"):
            strip = strip.astype(np.float32)
            signal = synth.synthesize(strip / 256, 1)
            synth.play(signal)
    
    cap.release()
    cv2.destroyAllWindows()
