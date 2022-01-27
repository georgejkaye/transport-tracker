from termcolor import cprint

debug = True


def debug(string):
    if debug:
        cprint(string, "yellow")


def error_msg(string):
    cprint(string, "red")
