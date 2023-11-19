from cv2 import Mat
import numpy as np
import numpy.typing as npt


Frame = Mat
Signal = npt.NDArray[np.float32]

__all__ = [
    "Frame",
    "Signal",
]
