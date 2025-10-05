import re
from pathlib import Path
from typing import Optional
from xmlrpc.client import boolean

from click import argument

from watcher.classes import PostgresFunction, PostgresFunctionArgument
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


def get_python_function_argument_for_postgres_function_argument(
    postgres_function_argument: PostgresFunctionArgument,
) -> str:
    python_type = get_python_type_for_postgres_type(
        postgres_function_argument.argument_type
    )
    if postgres_function_argument.argument_name.startswith("p_"):
        python_argument = postgres_function_argument.argument_name[2:]
    else:
        python_argument = postgres_function_argument.argument_name
    return f"{python_argument} : {python_type}"


def get_python_function_declaration_for_postgres_function(
    postgres_function: PostgresFunction, fetchall: bool
) -> str:
    arguments = [
        get_python_function_argument_for_postgres_function_argument(argument)
        for argument in postgres_function.function_args
    ]
    argument_string = ", ".join(arguments)
    return_type_string = get_python_type_for_postgres_type(
        postgres_function.function_return
    )
    if fetchall:
        return_type_string = f"list[{return_type_string}]"
    else:
        return_type_string = f"Optional[{return_type_string}]"
    declaration = f"def {postgres_function.function_name}(conn: Connection, {argument_string}) -> {return_type_string}:"
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
    return f'{tab}{tab}rows = cur.execute("SELECT * FROM {postgres_function.function_name}({argument_placeholder_string}))'


def get_python_fetchone() -> str:
    return f"{tab}{tab}return rows.fetchone()"


def get_python_fetchall() -> str:
    return f"{tab}{tab}return rows.fetchall()"


def get_python_for_postgres_function(
    postgres_function: PostgresFunction, fetchall: boolean
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


def get_python_for_postgres_function_file(file_path: str | Path) -> str:
    statements = get_statements_from_postgres_file(file_path, delimiter="$$;")
    postgres_functions = [
        postgres_function
        for statement in statements
        if (
            postgres_function := get_postgres_function_from_statement(statement)
        )
        is not None
    ]
    for postgres_function in postgres_functions:
        print(
            get_python_for_postgres_function(postgres_function, fetchall=True)
        )
        print()
    return ""


if __name__ == "__main__":
    get_python_for_postgres_function_file(
        "/home/george/docs/repos/train-tracker/db/code/4_select_bus.sql"
    )
