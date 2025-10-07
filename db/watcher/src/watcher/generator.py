from pathlib import Path
from typing import Callable

from watcher.classes import (
    PostgresObject,
    PythonPostgresModule,
    PythonPostgresModuleLookup,
    WatcherFilePaths,
)
from watcher.files import (
    get_path_for_module,
    get_python_module_name_for_postgres_file,
)


def get_postgres_module_for_postgres_file[T: PostgresObject](
    get_postgres_objects: Callable[[Path], list[T]],
    get_python_code_for_postgres_objects: Callable[
        [PythonPostgresModuleLookup, list[T]], str
    ],
    file_paths: WatcherFilePaths,
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    file_path: Path,
) -> tuple[PythonPostgresModuleLookup, PythonPostgresModule[T]]:
    postgres_objects = get_postgres_objects(file_path)
    python_code = get_python_code_for_postgres_objects(
        python_postgres_module_lookup, postgres_objects
    )
    python_module_name = get_python_module_name_for_postgres_file(
        file_paths.postgres_scripts_root_path,
        file_path,
        file_paths.python_output_module,
    )
    python_module_path = get_path_for_module(
        file_paths.python_source_root_path, python_module_name
    )
    for postgres_object in postgres_objects:
        python_name = postgres_object.get_python_name()
        python_postgres_module_lookup[python_name] = python_module_name
    python_postgres_module = PythonPostgresModule(
        python_module_path, python_module_name, postgres_objects, python_code
    )
    return (python_postgres_module_lookup, python_postgres_module)
