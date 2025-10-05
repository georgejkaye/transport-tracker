from pathlib import Path


def normalise_postgres_file_contents(file_contents: str) -> str:
    one_line_contents = file_contents.replace("\n", " ")
    space_normalised_contents = " ".join(one_line_contents.split())
    return space_normalised_contents


def get_statements_from_postgres_file_contents(
    file_contents: str, delimiter: str = ";"
) -> list[str]:
    normalised_file_contents = normalise_postgres_file_contents(file_contents)
    statements = normalised_file_contents.split(delimiter)
    return [statement.strip() for statement in statements]


def get_statements_from_postgres_file(
    file_path: str | Path, delimiter: str = ";"
) -> list[str]:
    with open(file_path, "r") as f:
        file_contents = f.read()
    return get_statements_from_postgres_file_contents(file_contents, delimiter)


postgres_to_python_type_dict = {
    "TEXT": "str",
    "INT": "int",
    "INTEGER": "int",
    "DECIMAL": "Decimal",
    "TIMESTAMP WITH TIME ZONE": "datetime",
    "TIMESTAMP WITHOUT TIME ZONE": "datetime",
    "INTERVAL": "timedelta",
    "DATERANGE": "Range",
}


def get_python_type_name_for_postgres_type_name(type_name: str) -> str:
    return "".join(x.capitalize() for x in type_name.lower().split("_"))


def get_python_type_for_base_postgres_type(base_type_string: str) -> str:
    if (
        base_python_type := postgres_to_python_type_dict.get(base_type_string)
    ) is not None:
        return base_python_type
    return get_python_type_name_for_postgres_type_name(base_type_string)


def get_python_type_for_postgres_type(type_string: str) -> str:
    is_array_type = type_string[-2:] == "[]"
    if is_array_type:
        base_type_string = type_string[:-2]
    else:
        base_type_string = type_string
    base_python_type = get_python_type_for_base_postgres_type(base_type_string)
    if is_array_type:
        return f"list[{base_python_type}]"
    return base_python_type
