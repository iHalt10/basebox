from typing import Callable
from typing import NewType
from typing import Union


class BaseBox:
    pass


KeyType = Union[str, int]
PrefixType = list[KeyType]
ValueType = object
ValidatedValueType = NewType("ValidatedValueType", object)
ValidatorType = Callable[[BaseBox, ValueType, PrefixType], ValidatedValueType]


class PrefixMixin:
    @property
    def prefix(self) -> PrefixType:
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: PrefixType) -> None:
        self._prefix = prefix

    def generate_key_string(self) -> str:
        s = ""
        for i, key in enumerate(self.prefix):
            if isinstance(key, str):
                s += f"{key}"
            if isinstance(key, int):
                s += f"[{key}]"
            if i + 1 != len(self.prefix) and isinstance(self.prefix[i + 1], str):
                s += f"."
        return s
