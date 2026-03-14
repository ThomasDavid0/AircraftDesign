from typing import TypeVar, Any
import numpy as np
import numpy.typing as npt


FloatArrayT = TypeVar("FloatArrayT", bound=npt.NDArray[np.floating[Any]])
