from typing import Optional
from api.utils.interactive import PickChoice
from questionary import Choice, text, confirm


def ask_text_question(message: str, default: str) -> Optional[str]:
    return text(message=message, default=default).ask()  # type: ignore


def ask_bool_question(message: str, default: bool = True) -> bool:
    return confirm(message, default=default).ask()  # type: ignore


def ask_select_question[T](
    message: str, choices: list[Choice], use_shortcuts: bool, instruction: str
) -> PickChoice[T]:
    return select(message, choices, use_shortcuts=use_shortcuts, instruction=instruction).ask()  # type: ignore
