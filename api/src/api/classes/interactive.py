from dataclasses import dataclass


@dataclass
class PickSingle[T]:
    choice: T


@dataclass
class PickMultiple[T]:
    choices: list[T]


@dataclass
class PickUnknown:
    pass


@dataclass
class PickCancel:
    pass


type PickChoice[T] = PickSingle[T] | PickMultiple[T] | PickUnknown | PickCancel
