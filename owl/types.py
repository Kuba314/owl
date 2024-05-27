from cv2.typing import MatLike
import numpy as np
import numpy.typing as npt


# Frame = MatLike
Frame = npt.NDArray[np.uint8]
Signal = npt.NDArray[np.float32]

__all__ = [
    "Frame",
    "Signal",
]
