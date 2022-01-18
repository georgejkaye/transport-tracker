from termcolor import cprint

debug = True


def debug(string):
    if debug:
        cprint(string, "red")
