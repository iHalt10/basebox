from __future__ import annotations

from collections.abc import ItemsView
from collections.abc import Iterator
from collections.abc import KeysView
from collections.abc import Mapping
from collections.abc import ValuesView
from typing import TYPE_CHECKING
from typing import Any
from typing import Type
from typing import cast

from .base_box import BaseBox
from .base_box import PrefixType
from .base_box import ValidatedValueType
from .base_box import ValueType
from .exceptions import BaseBoxForbidExtraKeyError
from .exceptions import BaseBoxNotImplementedError
from .exceptions import BaseBoxRequiredKeyError
from .exceptions import BaseBoxTypeError
from .exceptions import BaseBoxValueError
from .field import Field
from .field import Undefined
from .field import UndefinedType
from .typing_helper import get_ensured_validate_method
from .typing_helper import get_same_type_of_validator
from .typing_helper import resolve_annotations

_is_BaseBoxDict_defined = False


class BaseBoxDictMeta(type):
    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> BaseBoxDictMeta:
        fields: dict[str, Field] = {}

        for base in bases:
            if (
                _is_BaseBoxDict_defined
                and issubclass(base, BaseBoxDict)
                and base is not BaseBoxDict
            ):
                fields.update(base.__fields__)
                # deepcopy
        if _is_BaseBoxDict_defined and name != BaseBoxDict.__name__:
            annotations = resolve_annotations(namespace)
            for ann_name, ann_type in annotations.items():
                value = namespace.pop(ann_name, Undefined)
                inherited_validator = get_same_type_of_validator(
                    ann_name, ann_type, fields
                )

                try:
                    method = get_ensured_validate_method(
                        var_name=ann_name,
                        namespace=namespace,
                        return_type=cast(Type[ValidatedValueType], ann_type),
                    )
                except BaseBoxNotImplementedError:
                    if inherited_validator is None:
                        raise
                    method = inherited_validator

                fields[ann_name] = Field(
                    name=ann_name,
                    t=cast(Type[ValidatedValueType], ann_type),
                    validator=method,
                    default=value,
                )

        namespace["__fields__"] = fields
        return super().__new__(cls, name, bases, namespace)


class BaseBoxDict(BaseBox, metaclass=BaseBoxDictMeta):
    if TYPE_CHECKING:
        __fields__: dict[str, Field] = {}

    def __init__(
        self,
        value: dict[str, Any] = {},
        prefix: PrefixType = [],
    ):
        value = value or {}
        prefix = prefix or []
        self.__data__: dict[str, ValidatedValueType] = self.validate_all(value, prefix)

    def validate_all(
        self, value: ValueType, prefix: PrefixType
    ) -> dict[str, ValidatedValueType]:
        if not isinstance(value, dict):
            raise BaseBoxTypeError(prefix, value, expected_type=dict)
        value = cast(dict[str, ValueType], value.copy())
        result = {
            name: self.validate_value_with_prefix(field, value, prefix)
            for name, field in self.__fields__.items()
        }

        if bool(value):
            raise BaseBoxForbidExtraKeyError(prefix, list(value.keys()))

        return result

    def validate_value_with_prefix(
        self, field: Field, value: dict[str, ValueType], prefix: PrefixType
    ) -> ValidatedValueType:
        try:
            prefix.append(field.name)
            validated_value = field.validator(
                self, self.get_value_from_field(field, value, prefix), prefix
            )
            return validated_value
        except (BaseBoxTypeError, BaseBoxValueError) as e:
            if e.expected_type is UndefinedType:
                e.expected_type = field.t
            raise
        finally:
            prefix.pop()

    def get_value_from_field(
        self, field: Field, value: dict[str, ValueType], prefix: PrefixType
    ) -> ValueType:
        v = value.pop(field.name, Undefined)
        if v is Undefined:
            if field.is_required:
                raise BaseBoxRequiredKeyError(prefix)
            v = field.default
        return v

    def __getattr__(self, key: str) -> Any:
        if key in self.__data__:
            return self.__data__[key]
        return self.__dict__[key]

    def __setattr__(self, key: str, value: Any) -> None:
        # not use __fields__ or __data__ name
        field = self.__fields__.get(key, None)
        if field:
            self.__data__[key] = self.validate_value_with_prefix(field, value, [])
        else:
            self.__dict__[key] = value

    def __delattr__(self, key: str) -> None:
        if key not in self.__fields__ and key != "__data__":
            del self.__dict__[key]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Mapping) or isinstance(other, self.__class__):
            other = cast(Mapping[Any, Any], other)
            return dict(self.items()) == dict(other.items())
        return self.__data__ == other

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Mapping) or isinstance(other, self.__class__):
            other = cast(Mapping[Any, Any], other)
            return dict(self.items()) != dict(other.items())
        return self.__data__ != other

    def __contains__(self, key: str) -> bool:
        return key in self.__data__

    def __len__(self) -> int:
        return len(self.__data__)

    def __iter__(self) -> Iterator[Any]:
        return iter(self.__data__)

    def __copy__(self) -> BaseBoxDict:
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["__data__"] = self.__dict__["__data__"].copy()
        return inst

    def copy(self) -> BaseBoxDict:
        data = self.__data__
        self.__data__ = {}
        inst = self.__copy__()
        self.__data__ = data
        inst.__dict__["__data__"] = self.__dict__["__data__"].copy()
        return inst

    def keys(self) -> KeysView[Any]:
        return self.__data__.keys()

    def items(self) -> ItemsView[str, Any]:
        return self.__data__.items()

    def values(self) -> ValuesView[Any]:
        return self.__data__.values()


_is_BaseBoxDict_defined = True
