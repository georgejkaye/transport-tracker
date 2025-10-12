from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path


class PostgresObject:
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_python_name(self) -> str:
        pass


@dataclass
class PostgresTypeField:
    field_name: str
    field_type: str


@dataclass
class PostgresType(PostgresObject):
    type_name: str
    type_fields: list[PostgresTypeField]

    def get_name(self) -> str:
        return self.type_name

    def get_python_name(self) -> str:
        return "".join(
            x.capitalize() for x in self.type_name.lower().split("_")
        )


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
class PostgresFunction(PostgresObject):
    function_name: str
    function_return: str
    function_args: list[PostgresFunctionArgument]

    def get_name(self) -> str:
        return self.function_name

    def get_python_name(self) -> str:
        return self.function_name


@dataclass
class PostgresFileResult:
    type_files: list[Path]
    view_files: list[Path]
    function_files: list[Path]


type PythonPostgresModuleLookup = dict[str, str]
