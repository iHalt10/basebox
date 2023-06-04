from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Type
from typing import TypeVar
from typing import Union

if TYPE_CHECKING:
    from .base_box import ValidatedValueType
    from .base_box import ValidatorType


S = TypeVar("S")


class UndefinedType:
    def __repr__(self) -> str:
        return "Undefined"

    def __copy__(self: S) -> S:
        return self

    def __reduce__(self) -> str:
        return "Undefined"

    def __deepcopy__(self: S, _: Any) -> S:
        return self


Undefined = UndefinedType()


class Field:
    def __init__(
        self,
        name: str,
        t: Type[ValidatedValueType],
        validator: ValidatorType,
        default: Union[ValidatedValueType, UndefinedType] = Undefined,
    ):
        self.name = name
        self.t = t
        self.validator = validator
        self.default = default
        self.is_required = default is Undefined

    def __repr__(self) -> str:
        args: dict[str, Any] = {"name": self.name, "t": self.t}
        if not self.is_required:
            args["default"] = self.default
        return f"<Field: {repr(args)}>"
