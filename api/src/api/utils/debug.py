from termcolor import cprint

debug = False


def debug_msg(string: str) -> None:
    if debug:
        cprint(string, "yellow")


def error_msg(string: str):
    cprint(string, "red")
