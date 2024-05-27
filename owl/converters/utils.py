from typing import cast

import cv2
import numpy as np

from owl.types import Frame


def grayscale(frame: Frame) -> Frame:
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # type: ignore


def make_square(frame: Frame) -> Frame:
    height, width = frame.shape[:2]
    if width < height:
        height_offset = (height - width) // 2
        width_offset = 0
    else:
        height_offset = 0
        width_offset = (width - height) // 2

    side_length = min(width, height)
    squared_frame = frame[
        height_offset : height_offset + side_length,
        width_offset : width_offset + side_length,
    ]
    return cast(Frame, squared_frame)


def median_threshold(frame: Frame) -> Frame:
    assert len(frame.shape) == 2
    median = np.median(frame)
    return np.where(
        frame > median,
        np.full_like(frame, 255, dtype=np.uint8),
        np.zeros_like(frame, dtype=np.uint8),
    )


def square_resize(frame: Frame, side_length: int) -> Frame:
    return cv2.resize(
        frame,
        (side_length, side_length),
        interpolation=cv2.INTER_AREA,
    )  # type: ignore
