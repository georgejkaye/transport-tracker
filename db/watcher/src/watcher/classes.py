from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path

from watcher.pynames import (
    get_python_name_for_postgres_function_name,
    get_python_name_for_postgres_type_name,
)


class PostgresObject:
    @abstractmethod
    def get_name(self) -> str:
        pass


class PythonableObject:
    @abstractmethod
    def get_python_name(self) -> str:
        pass


class PythonablePostgresObject(PostgresObject, PythonableObject):
    pass


@dataclass
class PostgresTypeField:
    field_name: str
    field_type: str


@dataclass
class PostgresType(PythonablePostgresObject):
    type_name: str
    type_fields: list[PostgresTypeField]

    def get_name(self) -> str:
        return self.type_name

    def get_python_name(self) -> str:
        return get_python_name_for_postgres_type_name(self.type_name)


@dataclass
class PythonPostgresModule[T: PostgresObject]:
    module_name: str
    module_objects: list[T]
    python_code: str


@dataclass
class PostgresFunctionArgument:
    argument_name: str
    argument_type: str


@dataclass
class PostgresFunction(PythonablePostgresObject):
    function_name: str
    function_return: str
    function_args: list[PostgresFunctionArgument]

    def get_name(self) -> str:
        return self.function_name

    def get_python_name(self) -> str:
        return get_python_name_for_postgres_function_name(self.function_name)


@dataclass
class PostgresFileResult:
    type_files: list[Path]
    view_files: list[Path]
    function_files: list[Path]


type PythonPostgresModuleLookup = dict[str, str]

type PythonImportDict = dict[str, list[str]]
