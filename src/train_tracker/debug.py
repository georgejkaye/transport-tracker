from termcolor import cprint

debug = True


def debug_msg(string) -> None:
    if debug:
        cprint(string, "yellow")


def error_msg(string):
    cprint(string, "red")
