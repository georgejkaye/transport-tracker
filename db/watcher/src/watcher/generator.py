from pathlib import Path
from typing import Callable, Optional

from watcher.classes import (
    PythonablePostgresObject,
    PythonPostgresModule,
    PythonPostgresModuleLookup,
)
from watcher.files import (
    get_python_module_name_for_postgres_file,
)


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


def get_postgres_module_for_postgres_file[T: PythonablePostgresObject](
    get_postgres_object_for_statement: Callable[[str], Optional[T]],
    get_python_code_for_postgres_objects: Callable[
        [PythonPostgresModuleLookup, list[T]], str
    ],
    postgres_input_root_path: Path,
    python_output_root_module: str,
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    file_path: Path,
) -> tuple[PythonPostgresModuleLookup, PythonPostgresModule[T]]:
    postgres_statements = get_statements_from_postgres_file(file_path)
    postgres_objects = [
        postgres_object
        for statement in postgres_statements
        if (postgres_object := get_postgres_object_for_statement(statement))
        is not None
    ]
    python_code = get_python_code_for_postgres_objects(
        python_postgres_module_lookup, postgres_objects
    )
    python_module_name = get_python_module_name_for_postgres_file(
        postgres_input_root_path,
        file_path,
        python_output_root_module,
    )
    for postgres_object in postgres_objects:
        python_name = postgres_object.get_python_name()
        python_postgres_module_lookup[python_name] = python_module_name
    python_postgres_module = PythonPostgresModule(
        python_module_name, postgres_objects, python_code
    )
    return (python_postgres_module_lookup, python_postgres_module)
