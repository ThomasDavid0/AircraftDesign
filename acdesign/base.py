from inspect import getfullargspec
from typing import Self

class Modifiable:
    def modify(self, **kwargs) -> Self:
        return self.__class__(
            **{k: kwargs[k] if k in kwargs else getattr(self, k) for k in getfullargspec(self.__class__.__init__).args[1:]}
        )