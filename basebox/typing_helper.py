from __future__ import annotations

import sys
from inspect import FullArgSpec
from inspect import getfullargspec
from types import FunctionType
from types import GenericAlias
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Optional
from typing import Type
from typing import _eval_type  # type: ignore[attr-defined]
from typing import get_args
from typing import get_origin

from .base_box import PrefixType
from .base_box import ValidatedValueType
from .base_box import ValidatorType
from .base_box import ValueType
from .exceptions import BaseBoxNotImplementedError
from .exceptions import BaseBoxRuntimeError

if TYPE_CHECKING:
    from .field import Field


def resolve_annotations(namespace: dict[str, Any]) -> dict[str, Type[Any]]:
    raw_annotations = namespace.get("__annotations__", {})
    module_name = namespace.get("__module__", None)
    try:
        module = sys.modules[module_name]
    except KeyError:
        # happens occasionally, see https://github.com/samuelcolvin/pydantic/issues/2363
        raise BaseBoxRuntimeError(
            f"Unable to get '{module_name}' module from sys.modules."
        )
    base_globals: dict[str, Any] = module.__dict__

    return {
        name: _eval_type(t, base_globals, None) for name, t in raw_annotations.items()
    }


def get_ensured_validate_method(
    var_name: str, namespace: dict[str, Any], return_type: Type[ValidatedValueType]
) -> ValidatorType:
    method_name = f"validate_{var_name}"
    method = namespace.get(method_name, None)
    if isinstance(method, FunctionType):
        expected = FullArgSpec(
            args=["self", "value", "prefix"],
            varargs=None,
            varkw=None,
            defaults=None,
            kwonlyargs=[],
            kwonlydefaults=None,
            annotations={
                "value": ValueType,
                "prefix": PrefixType,
                "return": return_type,
            },
        )
        if getfullargspec(method) != expected:
            method = None

    if not isinstance(method, FunctionType):
        f = """Validator isn't implemented correctly.
  Expected method: def {0}(self, value: ValueType, prefix: PrefixType) -> {1}"""
        raise BaseBoxNotImplementedError(f.format(method_name, return_type))
    return method


def get_generic_types(
    target_cls: Type[object], namespace: dict[str, Any], cnt: int
) -> tuple[Type[Any], ...]:
    generics: Iterable[GenericAlias] = namespace.get("__orig_bases__", [])
    generic = {get_origin(t): t for t in generics}.get(target_cls, None)
    if generic is not None:
        generic_types = get_args(generic)
        if len(generic_types) == cnt:
            return generic_types
    raise BaseBoxNotImplementedError("Not correctly define generic.")


def get_same_type_of_validator(
    name: str, got_type: Type[Any], fields: dict[str, Field]
) -> Optional[ValidatorType]:
    inherited_validator: Optional[ValidatorType] = None

    if name in fields:
        field = fields[name]
        inherited_validator = field.validator
        if got_type != field.t:
            qualname = inherited_validator.__qualname__
            inherited_field_name = f"{qualname[:qualname.rfind('.')]}.{name}"
            f = """Different from the inherited '{0}' type.
  Got Type: {1}
  Expected Type: {2}"""
            raise BaseBoxNotImplementedError(
                f.format(inherited_field_name, got_type, field.t)
            )

    return inherited_validator
