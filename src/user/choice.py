from datetime import datetime, date, time
from typing import TypeVar, Optional
from structs.time import get_month_length, pad_front, to_time


def yes_or_no(prompt: str) -> bool:
    """
    Let the user say yes or no
    """
    choice = input(prompt + " (y/N) ")
    if choice == "y" or choice == "Y":
        return True
    return False


T = TypeVar('T')


def pick_from_list(choices: list[T], prompt: str, cancel: bool, display=lambda x: x) -> Optional[T]:
    """
    Let the user pick from a list of choices
    """
    for i, choice in enumerate(choices):
        print(str(i+1) + ": " + display(choice))
    if cancel:
        max_choice = len(choices) + 1
        # The last option is a cancel option, this returns None
        print(str(max_choice) + ": Cancel")
    else:
        max_choice = len(choices)
    while True:
        resp = input(prompt + " (1-" + str(max_choice) + "): ")
        try:
            resp_no = int(resp)
            if cancel and resp == len(choices) + 1:
                return None
            elif resp_no > 0 or resp_no < len(choices):
                return choices[resp_no - 1]
            print(f'Expected number 1-{max_choice} but got \'{resp_no}\'')
        except:
            print(f'Expected number 1-{max_choice} but got \'{resp_no}\'')


def get_input_no(prompt, upper=-1, default=-1) -> int:
    """
    Get a natural number of a given length from the user,
    optionally with an upper bound and a default value to use if no input is given
    """
    while True:
        prompt_string = prompt
        # Tell the user the default option
        if default != -1:
            prompt_string = prompt_string + " (" + str(default) + ")"
        prompt_string = prompt_string + ": "
        # Get input from the user
        string = input(prompt_string)
        # If the user gives an empty input, use the default if it exists
        if string == "" and default != -1:
            return int(default)
        try:
            nat = int(string)
            # Check the number is in the range
            if nat >= 0 and (upper == -1 or nat <= upper):
                return nat
            else:
                error_msg = "Expected number in range 0-"
                if upper != -1:
                    error_msg = error_msg + upper
                error_msg = error_msg + " but got " + string
                print(error_msg)
        except:
            print(f"Expected number but got '{string}'")


def get_date(start: datetime = None) -> date:
    if start is None:
        start = datetime.now()

    year = get_input_no("Year", 2022, pad_front(start.year, 4))
    month = get_input_no("Month", 12, pad_front(start.month, 2))
    max_days = get_month_length(month, year)
    day = get_input_no("Day", max_days, pad_front(start.day, 2))
    return date(year, month, day)


def get_time(start: datetime = None) -> time:
    if start is None:
        start = datetime.now()
    tt = pad_front(get_input_no("Time", 2359, pad_front(
        start.hour, 2) + pad_front(start.minute, 2)), 4)
    return to_time(tt)


def get_datetime(start: Optional[datetime]) -> datetime:
    date = get_date(start)
    time = get_time(start)
    return datetime(date.year, date.month, date.day, time.hour, time.minute)
