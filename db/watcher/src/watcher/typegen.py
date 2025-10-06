from pathlib import Path

from watcher.classes import (
    PostgresType,
    PostgresTypeField,
    PythonPostgresTypeModule,
    PythonPostgresTypeModuleDict,
)
from watcher.utils import (
    get_python_type_for_postgres_type,
    get_python_type_name_for_postgres_type_name,
    get_statements_from_postgres_file,
)

tab = "    "


def get_postgres_type_for_statement(
    statement: str,
) -> PostgresType:
    bracket_removed = statement.replace(")", "")
    string_split_at_bracket = bracket_removed.split("(", 1)
    postgres_create_type_clause = string_split_at_bracket[0]
    postgres_type_name = postgres_create_type_clause.split(" ")[2]
    postgres_type_field_clause = string_split_at_bracket[1]
    postgres_type_fields: list[PostgresTypeField] = []
    for type_clause in postgres_type_field_clause.split(","):
        type_clause_clauses = type_clause.strip().split(" ", 1)
        postgres_type_field_name = type_clause_clauses[0]
        postgres_type_field_type = type_clause_clauses[1]
        postgres_type_field = PostgresTypeField(
            postgres_type_field_name, postgres_type_field_type
        )
        postgres_type_fields.append(postgres_type_field)
    return PostgresType(postgres_type_name, postgres_type_fields)


def get_python_for_postgres_type(postgres_type: PostgresType) -> str:
    python_type_name = get_python_type_name_for_postgres_type_name(
        postgres_type.type_name
    )
    python_type_declaration = f"class {python_type_name}:"
    python_lines = ["@dataclass", python_type_declaration]
    for type_field in postgres_type.type_fields:
        python_type = get_python_type_for_postgres_type(type_field.field_type)
        python_type_field_str = f"{tab}{type_field.field_name}: {python_type}"
        python_lines.append(python_type_field_str)
    return "\n".join(python_lines)


def check_if_type_in_code(python_code_str: str, type_to_check: str) -> bool:
    return (
        f": {type_to_check}" in python_code_str
        or f"[{type_to_check}]" in python_code_str
    )


def get_imports_for_python_code_str(python_code_str: str) -> list[str]:
    python_imports: list[str] = ["from dataclasses import dataclass"]
    if "Optional[" in python_code_str:
        python_imports.append("from typing import Optional")
    if check_if_type_in_code(python_code_str, "datetime"):
        python_imports.append("from datetime import datetime")
    if check_if_type_in_code(python_code_str, "timedelta"):
        python_imports.append("from datetime import timedelta")
    if check_if_type_in_code(python_code_str, "Decimal"):
        python_imports.append("from decimal import Decimal")
    if check_if_type_in_code(python_code_str, "Range"):
        python_imports.append("from psycopg.types.range import Range")
    return python_imports


def get_python_code_for_postgres_types(
    postgres_types: list[PostgresType],
) -> str:
    python_type_codes = [
        get_python_for_postgres_type(postgres_type)
        for postgres_type in postgres_types
    ]
    python_code_str = "\n\n\n".join(python_type_codes)
    python_imports = get_imports_for_python_code_str(python_code_str)
    python_import_str = "\n".join(python_imports)
    return f"{python_import_str}\n\n{python_code_str}"


def get_python_module_name_for_postgres_type_file(
    source_base_path: Path,
    source_file_path: Path,
    output_root_module_name: str,
) -> str:
    source_relative_path = source_file_path.relative_to(source_base_path)
    module_name = source_relative_path.stem
    module_parent_names = list(source_relative_path.parts)[:-1]
    module_parts = [output_root_module_name]
    module_parts.extend(module_parent_names)
    module_parts.append(module_name)
    return ".".join(module_parts)


def get_python_module_path_for_python_module_name(
    root_path: Path, module_name: str
) -> Path:
    module_path = Path(module_name.replace(".", "/") + ".py")
    return root_path / module_path


def get_python_code_for_postgres_type_file(file_path: str | Path) -> str:
    statements = get_statements_from_postgres_file(file_path)
    postgres_types = [
        get_postgres_type_for_statement(statement) for statement in statements
    ]
    return get_python_code_for_postgres_types(postgres_types)


def get_postgres_types_for_postgres_type_file(
    file_path: Path,
) -> list[PostgresType]:
    statements = get_statements_from_postgres_file(file_path)
    postgres_types = [
        get_postgres_type_for_statement(statement) for statement in statements
    ]
    return postgres_types


def get_python_postgres_type_module_for_postgres_type_file(
    python_postgres_type_module_dict: PythonPostgresTypeModuleDict,
    source_root_path: Path,
    source_file_path: Path,
    output_root_path: Path,
    output_root_module_name: str,
) -> tuple[PythonPostgresTypeModuleDict, PythonPostgresTypeModule]:
    postgres_types = get_postgres_types_for_postgres_type_file(source_file_path)
    python_code = get_python_code_for_postgres_types(postgres_types)
    module_name = get_python_module_name_for_postgres_type_file(
        source_root_path,
        source_file_path,
        output_root_module_name,
    )
    module_path = get_python_module_path_for_python_module_name(
        output_root_path, module_name
    )
    for postgres_type in postgres_types:
        python_postgres_type_module_dict[postgres_type.type_name] = module_name
    python_postgres_type_module = PythonPostgresTypeModule(
        module_path,
        module_name,
        [
            get_python_type_for_postgres_type(postgres_type.type_name)
            for postgres_type in postgres_types
        ],
        python_code,
    )
    return (python_postgres_type_module_dict, python_postgres_type_module)


def get_python_postgres_type_modules_for_postgres_type_files(
    python_postgres_type_module_dict: PythonPostgresTypeModuleDict,
    source_root_path: Path,
    source_file_paths: list[Path],
    output_root_path: Path,
    output_root_module_name: str,
) -> tuple[PythonPostgresTypeModuleDict, list[PythonPostgresTypeModule]]:
    python_modules: list[PythonPostgresTypeModule] = []
    for source_file_path in source_file_paths:
        python_postgres_type_module_dict, python_module = (
            get_python_postgres_type_module_for_postgres_type_file(
                python_postgres_type_module_dict,
                source_root_path,
                source_file_path,
                output_root_path,
                output_root_module_name,
            )
        )
        python_modules.append(python_module)
    return (python_postgres_type_module_dict, python_modules)
