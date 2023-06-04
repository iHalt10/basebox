from __future__ import annotations

from abc import ABCMeta
from abc import abstractmethod
from collections.abc import MutableSequence
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Type
from typing import TypeVar
from typing import Union
from typing import cast
from typing import overload

from .base_box import PrefixType
from .base_box import ValidatedValueType
from .base_box import ValueType
from .exceptions import BaseBoxTypeError
from .exceptions import BaseBoxValueError
from .field import UndefinedType
from .typing_helper import get_ensured_validate_method
from .typing_helper import get_generic_types

T = TypeVar("T")
_is_BaseBoxList_defined = False


class BaseBoxListMeta(type):
    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> BaseBoxListMeta:
        if _is_BaseBoxList_defined and name != BaseBoxList.__name__:
            generic_types = get_generic_types(BaseBoxList, namespace, 1)

            get_ensured_validate_method(
                var_name="item",
                namespace=namespace,
                return_type=cast(Type[ValidatedValueType], generic_types[0]),
            )
            namespace["__generic_type__"] = generic_types[0]

        new_cls = super().__new__(cls, name, bases, namespace)
        return new_cls


class CombinedMeta(ABCMeta, BaseBoxListMeta):
    pass


class BaseBoxList(MutableSequence[T], metaclass=CombinedMeta):
    if TYPE_CHECKING:
        __generic_type__: Type[Any]

    def __init__(
        self,
        value: Iterable[Any] = [],
        prefix: PrefixType = [],
    ):
        value = value or []
        prefix = prefix or []
        self.__data__: list[T] = self.validate_all(value, prefix)

    @abstractmethod
    def validate_item(self, value: ValueType, prefix: PrefixType) -> T:
        raise NotImplementedError()

    def validate_all(self, value: ValueType, prefix: PrefixType) -> list[T]:
        if not isinstance(value, Iterable):
            raise BaseBoxTypeError(prefix, value, expected_type=Iterable)

        value = cast(Iterable[ValueType], value)
        return [
            self.validate_item_with_prefix(i, item, prefix)
            for i, item in enumerate(value)
        ]

    def validate_item_with_prefix(
        self, i: int, value: ValueType, prefix: PrefixType
    ) -> T:
        try:
            prefix.append(i)
            validated_value = self.validate_item(value, prefix)
            return validated_value
        except (BaseBoxTypeError, BaseBoxValueError) as e:
            if e.expected_type is UndefinedType:
                e.expected_type = self.__generic_type__
            raise
        finally:
            prefix.pop()

    def __lt__(self, other: Union[list[T], BaseBoxList[T]]) -> bool:
        # TypeError
        return self.__data__ < self.__cast(other)

    def __le__(self, other: Union[list[T], BaseBoxList[T]]) -> bool:
        # TypeError
        return self.__data__ <= self.__cast(other)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BaseBoxList):
            other = cast(BaseBoxList[T], other)
            return self.__data__ == other.__data__
        return self.__data__ == other

    def __ne__(self, other: object) -> bool:
        if isinstance(other, BaseBoxList):
            other = cast(BaseBoxList[T], other)
            return self.__data__ != other.__data__
        return self.__data__ != other

    def __gt__(self, other: Union[list[T], BaseBoxList[T]]) -> bool:
        # TypeError
        return self.__data__ > self.__cast(other)

    def __ge__(self, other: Union[list[T], BaseBoxList[T]]) -> bool:
        # TypeError
        return self.__data__ >= self.__cast(other)

    def __cast(self, other: Union[list[T], BaseBoxList[T]]) -> list[T]:
        if isinstance(other, BaseBoxList):
            return other.__data__
        return other

    def __contains__(self, item: object) -> bool:
        return item in self.__data__

    def __len__(self) -> int:
        return len(self.__data__)

    @overload
    def __getitem__(self, index: int) -> T:
        pass

    @overload
    def __getitem__(self, index: slice) -> BaseBoxList[T]:
        pass

    def __getitem__(self, index: Union[int, slice]) -> Union[T, BaseBoxList[T]]:
        # TypeError
        # IndexError
        if isinstance(index, int):
            return self.__data__[index]
        else:
            new_list = self.__class__()
            new_list.__data__ = self.__data__[index]
            return new_list

    def __setitem__(self, index: Union[int, slice], item: Union[T, Iterable[T]]) -> None:
        # TypeError
        # IndexError
        if isinstance(index, int):
            self.__data__[index] = self.validate_item_with_prefix(index, item, [])
        else:
            self.__data__[index] = self.validate_all(item, [])

    def __delitem__(self, idx: Union[int, slice]) -> None:
        # TypeError
        # IndexError
        del self.__data__[idx]

    def __add__(self, other: Iterable[T]) -> BaseBoxList[T]:
        new_list = self.copy()
        new_list.__data__ += new_list.validate_all(other, [])
        return new_list

    def __radd__(self, other: Iterable[T]) -> BaseBoxList[T]:
        new_list = self.__class__(other)
        new_list.__data__ += self.__data__
        return new_list

    def __iadd__(self, other: Iterable[T]) -> BaseBoxList[T]:
        self.__data__ += self.validate_all(other, [])
        return self

    def __mul__(self, n: int) -> BaseBoxList[T]:
        # TypeError int
        new_list = self.copy()
        new_list.__data__ *= n
        return new_list

    __rmul__ = __mul__

    def __imul__(self, n: int) -> BaseBoxList[T]:
        # TypeError int
        self.__data__ *= n
        return self

    def __copy__(self) -> BaseBoxList[T]:
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["__data__"] = self.__dict__["__data__"][:]
        return inst

    def append(self, value: T) -> None:
        validated_value = self.validate_item_with_prefix(len(self), value, [])
        self.__data__.append(validated_value)

    def insert(self, index: int, value: T) -> None:
        validated_value = self.validate_item_with_prefix(index, value, [])
        self.__data__.insert(index, validated_value)

    def pop(self, index: int = -1) -> T:
        # TypeError int
        return self.__data__.pop(index)

    def remove(self, value: T) -> None:
        # ValueError item
        self.__data__.remove(value)

    def clear(self) -> None:
        self.__data__.clear()

    def copy(self) -> BaseBoxList[T]:
        new_list = self.__class__()
        new_list.__data__ = self.__data__.copy()
        return new_list

    def count(self, value: Any) -> int:
        return self.__data__.count(value)

    def index(self, value: T, *args: int) -> int:
        # ValueError item
        return self.__data__.index(value, *args)

    def reverse(self) -> None:
        self.__data__.reverse()

    def sort(self, *args: Any, **kwargs: Any) -> None:
        self.__data__.sort(*args, **kwargs)

    def extend(self, values: Iterable[T]) -> None:
        validated_values = self.validate_all(values, [])
        self.__data__.extend(validated_values)


_is_BaseBoxList_defined = True
