import sys
from pathlib import Path
from typing import Callable

from watcher.classes import (
    PostgresFunction,
    PostgresObject,
    PostgresType,
    PythonPostgresModule,
    PythonPostgresModuleLookup,
)
from watcher.files import (
    clean_output_directory,
    create_py_typed_files_in_directory,
    get_db_script_files,
    get_postgres_files_in_directory,
    write_python_file,
)
from watcher.funcgen import (
    get_python_postgres_module_for_postgres_function_file,
)
from watcher.runner import run_in_script_file
from watcher.typegen import get_python_postgres_module_for_postgres_type_file


def process_script_file[T: PostgresObject](
    postgres_input_root_path: Path,
    python_output_root_module: str,
    python_output_root_path: Path,
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    get_script_file_module: Callable[
        [Path, str, PythonPostgresModuleLookup, Path],
        tuple[PythonPostgresModuleLookup, PythonPostgresModule[T]],
    ],
    script_file: Path,
) -> tuple[PythonPostgresModuleLookup, PythonPostgresModule[T]]:
    run_in_script_file(script_file)
    python_postgres_module_lookup, script_file_module = get_script_file_module(
        postgres_input_root_path,
        python_output_root_module,
        python_postgres_module_lookup,
        script_file,
    )
    write_python_file(
        python_output_root_path,
        script_file_module.module_name,
        script_file_module.python_code,
    )
    return python_postgres_module_lookup, script_file_module


def process_type_script_file(
    postgres_input_root_path: Path,
    python_output_root_module: str,
    python_output_root_path: Path,
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    script_file: Path,
) -> tuple[PythonPostgresModuleLookup, PythonPostgresModule[PostgresType]]:
    return process_script_file(
        postgres_input_root_path,
        python_output_root_module,
        python_output_root_path,
        python_postgres_module_lookup,
        get_python_postgres_module_for_postgres_type_file,
        script_file,
    )


def process_view_script_file(script_file: Path):
    run_in_script_file(script_file)


def process_function_script_file(
    postgres_input_root_path: Path,
    python_output_root_module: str,
    python_output_root_path: Path,
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    script_file: Path,
) -> tuple[PythonPostgresModuleLookup, PythonPostgresModule[PostgresFunction]]:
    return process_script_file(
        postgres_input_root_path,
        python_output_root_module,
        python_output_root_path,
        python_postgres_module_lookup,
        get_python_postgres_module_for_postgres_function_file,
        script_file,
    )


def process_internal_script_files(internal_scripts_path: Path):
    internal_files = get_db_script_files(internal_scripts_path)
    for file in internal_files:
        run_in_script_file(file)


def process_user_script_files(
    python_source_root: Path,
    output_code_module: str,
    user_scripts_path: Path,
):
    user_files = get_postgres_files_in_directory(user_scripts_path)
    python_postgres_module_lookup: PythonPostgresModuleLookup = {}
    for file in user_files.type_files:
        python_postgres_module_lookup, _ = process_type_script_file(
            user_scripts_path,
            output_code_module,
            python_source_root,
            python_postgres_module_lookup,
            file,
        )
    for file in user_files.view_files:
        process_view_script_file(file)
    for file in user_files.function_files:
        process_function_script_file(
            user_scripts_path,
            output_code_module,
            python_source_root,
            python_postgres_module_lookup,
            file,
        )


def process_all_script_files(
    internal_scripts_path: Path,
    user_scripts_path: Path,
    python_source_root: Path,
    output_code_module: str,
):
    clean_output_directory(python_source_root, output_code_module)
    process_internal_script_files(internal_scripts_path)
    process_user_script_files(
        python_source_root, output_code_module, user_scripts_path
    )
    create_py_typed_files_in_directory(python_source_root, output_code_module)


if __name__ == "__main__":
    internal_scripts_path = Path(sys.argv[1])
    user_scripts_path = Path(sys.argv[2])
    python_source_root = Path(sys.argv[3])
    output_code_module = sys.argv[4]
    process_all_script_files(
        internal_scripts_path,
        user_scripts_path,
        python_source_root,
        output_code_module,
    )
