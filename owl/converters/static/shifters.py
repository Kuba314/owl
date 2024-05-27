from dataclasses import dataclass

import cv2
import numpy as np

from owl.events import notify
from owl.frequency_curve import FrequencyCurve
from owl.types import Frame

from ..utils import grayscale, make_square, median_threshold, square_resize
from .base import Sine, SineConverter


def kmeans(
    frame: Frame,
    k: int,
    # intensity_levels: int,
    attempts: int = 5,
    count_criterion: int | None = 50,
    eps_criterion: float | None = 0.1,
) -> dict[tuple[float, float], float]:
    # weighted k-means
    # weight_multiplier = intensity_levels / 256
    data: list[tuple[int, int]] = [(x, y) for y, row in enumerate(frame) for x, v in enumerate(row)]
    # for y, row in enumerate(frame):
    #     for x, v in enumerate(row):
    #         data.extend((x, y) for _ in range(int(v * weight_multiplier)))

    if not data:
        return {}

    criteria_flags = 0
    if count_criterion is not None:
        criteria_flags += cv2.TermCriteria_COUNT
    if eps_criterion is not None:
        criteria_flags += cv2.TermCriteria_EPS

    _, classes, centers = cv2.kmeans(
        np.array(data, dtype=np.float32),
        k,
        None,  # type: ignore
        criteria=(criteria_flags, count_criterion or 0, eps_criterion or 0),
        attempts=attempts,
        flags=0,
    )
    center_counts: dict[tuple[int, int], int] = {}
    for class_ in classes:
        center = tuple(centers[class_[0]])
        if center not in center_counts:
            center_counts[center] = 0
        center_counts[center] += 1
    total_count = sum(center_counts.values())
    return {center: count / total_count for center, count in center_counts.items()}


@dataclass
class ShiftersConverter(SineConverter):
    """K-means brightest points on frequency curve"""

    frequency_curve: FrequencyCurve
    intensity_levels: int

    def _extract_sines(self, frame: Frame) -> list[Sine]:
        side_length = self.frequency_curve.side_length
        frame = make_square(frame)
        original_size_length = frame.shape[0]
        frame = square_resize(frame, side_length)
        frame = grayscale(frame)
        notify("converter:frame:pre", square_resize(frame, original_size_length))
        frame = median_threshold(frame)

        # TODO: threshold wiht 50% (80%?), then extract islands and map their size to volume
        center_weights = kmeans(frame, self.sine_count)
        for center, weight in center_weights.items():
            cv2.circle(frame, list(map(lambda x: int(x/side_length*frame.shape[0]), center)), int(weight**2 * 50), color=(0, 0, 0))
        notify("converter:frame:post", square_resize(frame, original_size_length))

        sines: list[Sine] = []
        for (x, y), weight in center_weights.items():
            point = (int(x), int(y))

            frequency = self.frequency_curve.get_frequency(point)
            if frequency is None:
                raise Exception(f"k-means: Point {point} out of curve bounds ({side_length})")
            sines.append(Sine(frequency, volume=weight**2))

        sines.sort(key=lambda x: x.frequency)
        return sines
