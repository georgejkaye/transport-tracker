from pathlib import Path
from typing import Optional


def normalise_postgres_file_contents(file_contents: str) -> str:
    one_line_contents = file_contents.replace("\n", " ")
    space_normalised_contents = " ".join(one_line_contents.split())
    return space_normalised_contents


def get_statements_from_postgres_file_contents(
    file_contents: str, delimiter: str = ";"
) -> list[str]:
    normalised_file_contents = normalise_postgres_file_contents(file_contents)
    statements = normalised_file_contents.split(delimiter)
    return [statement.strip() for statement in statements if len(statement) > 0]


def get_statements_from_postgres_file(
    file_path: str | Path, delimiter: str = ";"
) -> list[str]:
    with open(file_path, "r") as f:
        file_contents = f.read()
    return get_statements_from_postgres_file_contents(file_contents, delimiter)


postgres_to_python_type_dict = {
    "VOID": "None",
    "TEXT": "Optional[str]",
    "TEXT_NOTNULL": "str",
    "INT": "Optional[int]",
    "INTEGER": "Optional[int]",
    "INTEGER_NOTNULL": "int",
    "BIGINT": "Optional[int]",
    "BIGINT_NOTNULL": "int",
    "DECIMAL": "Optional[Decimal]",
    "DECIMAL_NOTNULL": "Decimal",
    "TIMESTAMP WITH TIME ZONE": "Optional[datetime]",
    "TIMESTAMP WITHOUT TIME ZONE": "Optional[datetime]",
    "TIMESTAMP_NOTNULL": "datetime",
    "INTERVAL": "Optional[timedelta]",
    "INTERVAL_NOTNULL": "timedelta",
    "DATERANGE": "Optional[Range]",
    "DATERANGE_NOTNULL": "Range",
    "BOOLEAN": "Optional[bool]",
    "BOOLEAN_NOTNULL": "bool",
}


def get_python_type_for_base_type_of_postgres_type(
    postgres_type_name: str,
) -> Optional[str]:
    if postgres_type_name[-2:] == "[]":
        postgres_type_name = postgres_type_name[:-2]
    return postgres_to_python_type_dict.get(postgres_type_name)


def get_python_type_name_for_postgres_type_name(type_name: str) -> str:
    return "".join(x.capitalize() for x in type_name.lower().split("_"))


def get_python_type_for_postgres_base_type(base_type_string: str) -> str:
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
    base_python_type = get_python_type_for_postgres_base_type(base_type_string)
    if is_array_type:
        return f"list[{base_python_type}]"
    return base_python_type
