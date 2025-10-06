import re
from pathlib import Path
from typing import Optional

from watcher.classes import (
    PostgresFunction,
    PostgresFunctionArgument,
    PythonPostgresTypeModuleDict,
)
from watcher.typegen import (
    get_python_postgres_type_modules_for_postgres_type_files,
)
from watcher.utils import (
    get_python_type_for_postgres_type,
    get_statements_from_postgres_file,
)

tab = "    "
postgres_function_regex = r"CREATE(?: OR REPLACE)? FUNCTION ([A-z_]*)(?: )?\((.*)\).*RETURNS(?: SETOF)? (.*?) "


def get_postgres_function_args_from_argument_str(
    argument_str: str,
) -> list[PostgresFunctionArgument]:
    if argument_str == "":
        return []
    function_arg_split = argument_str.split(",")
    postgres_function_args: list[PostgresFunctionArgument] = []
    for function_arg in function_arg_split:
        function_arg_split = function_arg.split()
        function_arg_name = function_arg_split[0]
        function_arg_type = function_arg_split[1]
        postgres_function_arg = PostgresFunctionArgument(
            function_arg_name, function_arg_type
        )
        postgres_function_args.append(postgres_function_arg)
    return postgres_function_args


def get_postgres_function_from_statement(
    statement: str,
) -> Optional[PostgresFunction]:
    function_matches = re.match(postgres_function_regex, statement)
    if function_matches is None:
        return None
    function_name = function_matches.group(1)
    function_args_str = function_matches.group(2)
    function_return = function_matches.group(3)
    postgres_function_args = get_postgres_function_args_from_argument_str(
        function_args_str
    )
    return PostgresFunction(
        function_name, function_return, postgres_function_args
    )


def get_python_function_argument_name_for_postgres_function_argument_name(
    postgres_function_argument_name: str,
) -> str:
    if postgres_function_argument_name.startswith("p_"):
        return postgres_function_argument_name[2:]
    else:
        return postgres_function_argument_name


def get_python_function_argument_for_postgres_function_argument(
    postgres_function_argument: PostgresFunctionArgument,
) -> str:
    python_type = get_python_type_for_postgres_type(
        postgres_function_argument.argument_type
    )
    python_argument_name = (
        get_python_function_argument_name_for_postgres_function_argument_name(
            postgres_function_argument.argument_name
        )
    )
    return f"{python_argument_name} : {python_type}"


def get_python_function_declaration_for_postgres_function(
    postgres_function: PostgresFunction, fetchall: bool
) -> str:
    arguments = [
        get_python_function_argument_for_postgres_function_argument(argument)
        for argument in postgres_function.function_args
    ]
    arguments = ["conn: Connection"] + arguments
    argument_string = f",\n{tab}".join(arguments)
    return_type_string = get_python_type_for_postgres_type(
        postgres_function.function_return
    )
    if fetchall:
        return_type_string = f"list[{return_type_string}]"
    else:
        return_type_string = f"Optional[{return_type_string}]"
    declaration = f"def {postgres_function.function_name}(\n{tab}{argument_string}\n) -> {return_type_string}:"
    return declaration


def get_python_cursor_initialisation_for_postgres_function(
    postgres_function: PostgresFunction,
) -> str:
    python_return_type = get_python_type_for_postgres_type(
        postgres_function.function_return
    )
    return f"{tab}with conn.cursor(row_factory=class_row({python_return_type})) as cur:"


def get_python_cursor_execution_for_postgres_function(
    postgres_function: PostgresFunction,
) -> str:
    argument_placeholder_string = ", ".join(
        ["%s"] * len(postgres_function.function_args)
    )
    argument_list = f"[{', '.join([get_python_function_argument_name_for_postgres_function_argument_name(function_arg.argument_name) for function_arg in postgres_function.function_args])}]"
    return f'{tab}{tab}rows = cur.execute(\n{tab}{tab}{tab}"SELECT * FROM {postgres_function.function_name}({argument_placeholder_string})",\n{tab}{tab}{tab}{argument_list}\n{tab}{tab})'


def get_python_fetchone() -> str:
    return f"{tab}{tab}return rows.fetchone()"


def get_python_fetchall() -> str:
    return f"{tab}{tab}return rows.fetchall()"


def get_python_for_postgres_function(
    postgres_function: PostgresFunction, fetchall: bool
) -> str:
    python_function_declaration = (
        get_python_function_declaration_for_postgres_function(
            postgres_function, fetchall
        )
    )
    python_cursor_initialisation = (
        get_python_cursor_initialisation_for_postgres_function(
            postgres_function
        )
    )
    python_cursor_execution = get_python_cursor_execution_for_postgres_function(
        postgres_function
    )
    if fetchall:
        python_result_fetching = get_python_fetchall()
    else:
        python_result_fetching = get_python_fetchone()
    return f"{python_function_declaration}\n{python_cursor_initialisation}\n{python_cursor_execution}\n{python_result_fetching}"


def get_imports_for_postgres_function_file(
    python_postgres_type_module_dict: PythonPostgresTypeModuleDict,
    postgres_functions: list[PostgresFunction],
) -> str:
    psycopg_imports = [
        "from typing import Optional",
        "from psycopg import Connection",
        "from psycopg.rows import class_row",
    ]
    types_used: list[str] = []
    # TODO Combine and alphabetise imports
    for postgres_function in postgres_functions:
        type_module = python_postgres_type_module_dict.get(
            postgres_function.function_return
        )
        if (
            type_module is not None
            and postgres_function.function_return not in types_used
        ):
            types_used.append(postgres_function.function_return)
    type_imports = [
        f"from {python_postgres_type_module_dict[type_used]} import {get_python_type_for_postgres_type(type_used)}"
        for type_used in types_used
    ]
    return f"{'\n'.join(psycopg_imports)}\n\n{'\n'.join(type_imports)}"


def get_python_for_postgres_function_file(
    python_postgres_type_module_dict: PythonPostgresTypeModuleDict,
    file_path: str | Path,
) -> str:
    statements = get_statements_from_postgres_file(file_path, delimiter="$$;")
    postgres_functions = [
        postgres_function
        for statement in statements
        if (
            postgres_function := get_postgres_function_from_statement(statement)
        )
        is not None
    ]
    print(
        get_imports_for_postgres_function_file(
            python_postgres_type_module_dict, postgres_functions
        )
    )
    print()
    for postgres_function in postgres_functions:
        print(
            get_python_for_postgres_function(postgres_function, fetchall=True)
        )
        print()
    return ""


if __name__ == "__main__":
    type_dict, modules = (
        get_python_postgres_type_modules_for_postgres_type_files(
            {},
            Path("/home/george/docs/repos/train-tracker/db/code/"),
            [
                Path(
                    "/home/george/docs/repos/train-tracker/db/code/1_types_2_bus.sql"
                )
            ],
            Path("/home/george/docs/repos/train-tracker/api/src"),
            "api.db",
        )
    )
    get_python_for_postgres_function_file(
        type_dict,
        "/home/george/docs/repos/train-tracker/db/code/4_select_bus.sql",
    )
