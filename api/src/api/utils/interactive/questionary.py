from typing import Any, Callable, Optional, cast

from questionary import Choice, confirm, select, text

from api.utils.interactive.classes import PickChoice


def ask_text_question(
    message: str, default: str, validate: Callable[[str], bool] = lambda _: True
) -> Optional[str]:
    return cast(
        Optional[str],
        cast(Any, text)(
            message=message, default=default, validate=validate
        ).ask(),
    )


def ask_bool_question(message: str, default: bool = True) -> bool:
    return cast(bool, cast(Any, confirm)(message, default=default).ask())


def ask_select_question[T](
    message: str, choices: list[Choice], use_shortcuts: bool, instruction: str
) -> PickChoice[T]:
    return cast(
        PickChoice[T],
        cast(Any, select)(
            message,
            choices,
            use_shortcuts=use_shortcuts,
            instruction=instruction,
        ).ask(),
    )
