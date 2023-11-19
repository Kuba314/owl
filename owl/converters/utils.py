from typing import cast

from owl.types import Frame


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
