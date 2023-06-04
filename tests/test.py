from basebox import BaseBoxDict
from basebox import BaseBoxTypeError
from basebox import PrefixType
from basebox import ValueType


class Preferences(BaseBoxDict):
    name: str
    cnt: int = 0

    def validate_name(self, value: ValueType, prefix: PrefixType) -> str:
        if not isinstance(value, str):
            raise BaseBoxTypeError(prefix, value, "Must be a str type.", [str])
        return value

    def validate_cnt(self, value: ValueType, prefix: PrefixType) -> int:
        if not isinstance(value, int):
            raise BaseBoxTypeError(prefix, value, "Must be a str type.", [int])
        return value
