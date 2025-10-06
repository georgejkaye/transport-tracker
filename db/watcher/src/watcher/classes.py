from dataclasses import dataclass
from pathlib import Path


@dataclass
class PostgresTypeField:
    field_name: str
    field_type: str


@dataclass
class PostgresType:
    type_name: str
    type_fields: list[PostgresTypeField]


@dataclass
class PythonPostgresTypeModule:
    module_path: Path
    module_name: str
    module_types: list[str]
    python_code: str


type PythonPostgresTypeModuleDict = dict[str, str]


@dataclass
class PostgresFunctionArgument:
    argument_name: str
    argument_type: str


@dataclass
class PostgresFunction:
    function_name: str
    function_return: str
    function_args: list[PostgresFunctionArgument]
