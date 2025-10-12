from typing import Optional

from watcher.pynames import get_python_name_for_postgres_type_name

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


def get_python_type_for_postgres_base_type(base_type_string: str) -> str:
    if (
        base_python_type := postgres_to_python_type_dict.get(base_type_string)
    ) is not None:
        return base_python_type
    return get_python_name_for_postgres_type_name(base_type_string)


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


def update_python_type_import_dict(
    imports_dict: dict[str, list[str]], type_module: str, type_name: str
) -> dict[str, list[str]]:
    module_result = imports_dict.get(type_module)
    if module_result is None:
        imports_dict[type_module] = [type_name]
        return imports_dict
    if type_name in module_result:
        return imports_dict
    imports_dict[type_module].append(type_name)
    return imports_dict
