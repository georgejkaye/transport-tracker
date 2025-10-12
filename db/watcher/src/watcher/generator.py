from pathlib import Path
from typing import Callable

from watcher.classes import (
    PostgresObject,
    PythonPostgresModule,
    PythonPostgresModuleLookup,
)
from watcher.files import (
    get_python_module_name_for_postgres_file,
)


def get_postgres_module_for_postgres_file[T: PostgresObject](
    get_postgres_objects: Callable[[Path], list[T]],
    get_python_code_for_postgres_objects: Callable[
        [PythonPostgresModuleLookup, list[T]], str
    ],
    postgres_input_root_path: Path,
    python_output_root_module: str,
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    file_path: Path,
) -> tuple[PythonPostgresModuleLookup, PythonPostgresModule[T]]:
    postgres_objects = get_postgres_objects(file_path)
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
