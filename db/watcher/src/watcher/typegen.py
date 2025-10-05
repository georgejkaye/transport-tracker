from pathlib import Path

from watcher.classes import PostgresType, PostgresTypeField
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
        type_clause_clauses = type_clause.strip().split(" ")
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


def get_imports_for_python_code_str(python_code_str: str) -> list[str]:
    python_imports: list[str] = ["from dataclasses import dataclass"]
    if ": datetime" in python_code_str:
        python_imports.append("from datetime import datetime")
    if ": timedelta" in python_code_str:
        python_imports.append("from datetime import timedelta")
    if ": Decimal" in python_code_str:
        python_imports.append("from decimal import Decimal")
    if ": Range" in python_code_str:
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


def get_python_code_for_postgres_type_file(file_path: str | Path) -> str:
    statements = get_statements_from_postgres_file(file_path)
    postgres_types = [
        get_postgres_type_for_statement(statement) for statement in statements
    ]
    return get_python_code_for_postgres_types(postgres_types)
