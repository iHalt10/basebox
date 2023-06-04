from typing import Any
from typing import Type

from .base_box import PrefixMixin
from .base_box import PrefixType
from .field import UndefinedType


class BaseBoxRuntimeError(RuntimeError):
    pass


class BaseBoxNotImplementedError(NotImplementedError):
    pass


class BaseBoxGeneralError(Exception, PrefixMixin):
    def __init__(
        self,
        prefix: PrefixType,
        value: Any,
        msg: str = "",
        allowed_extra_types: list[Type[Any]] = [],
        expected_type: Type[Any] = UndefinedType,
    ):
        self.value = value
        self.value_type = type(value)
        self.prefix = prefix.copy()
        self.msg: str = msg
        self.allowed_extra_types = allowed_extra_types or []
        self.expected_type = expected_type

    def __str__(self) -> str:
        f = """{0}
  Prefix: {1}
  Got Value: {2}
  Got Type: {3}
  Expected Type: {4}
  Allowed Extra Types: {5}"""
        return f.format(
            self.msg,
            self.prefix,
            self.value,
            self.value_type,
            self.expected_type,
            self.allowed_extra_types,
        )


class BaseBoxTypeError(BaseBoxGeneralError, TypeError):
    pass


class BaseBoxValueError(BaseBoxGeneralError, ValueError):
    pass


class BaseBoxRequiredKeyError(KeyError, PrefixMixin):
    def __init__(self, prefix: PrefixType):
        self.prefix = prefix.copy()
        self.required_key = prefix[-1]

    def __str__(self) -> str:
        return f"Required {self.required_key} key\n  Prefix: {self.prefix}"


class BaseBoxForbidExtraKeyError(KeyError, PrefixMixin):
    def __init__(self, prefix: PrefixType, extra_keys: list[str]):
        self.prefix = prefix.copy()
        self.extra_keys = extra_keys

    def __str__(self) -> str:
        return f"Forbid extra {self.extra_keys} keys\n  Prefix: {self.prefix}"
