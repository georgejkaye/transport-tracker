from typing import Callable, Optional


def get_value_or_none[T, U](
    get: Callable[[T], U | None], obj: T | None
) -> U | None:
    if obj is None:
        return None
    return get(obj)


def apply_to_optional[T, U](
    t: Optional[T], fn: Callable[[T], U]
) -> Optional[U]:
    if t is None:
        return None
    return fn(t)
