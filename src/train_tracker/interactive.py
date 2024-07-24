def thick_line(length: int = 80):
    print("=" * length)


def thin_line(length: int = 80):
    print("-" * length)


def space():
    print()


def message(msg: str):
    print(msg)


def option(number: int, choice: str):
    print(f"{number}: {choice}")


def header(msg: str, length: int = 80):
    thick_line(length)
    message(msg)
    thick_line(length)
    space()


def subheader(msg: str, length: int = 80):
    thin_line(length)
    message(msg)
    thin_line(length)
    space()
