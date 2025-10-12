import re
import sys
from pathlib import Path
from typing import Optional

from watcher.classes import (
    PostgresFunction,
    PostgresFunctionArgument,
    PythonPostgresModule,
    PythonPostgresModuleLookup,
)
from watcher.generator import get_postgres_module_for_postgres_file
from watcher.utils import (
    get_python_type_for_base_type_of_postgres_type,
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
    if return_type_string == "None":
        return_type_string = "None"
        function_name = postgres_function.function_name
    elif fetchall:
        return_type_string = f"list[{return_type_string}]"
        function_name = f"{postgres_function.function_name}_fetchall"
    else:
        return_type_string = f"Optional[{return_type_string}]"
        function_name = f"{postgres_function.function_name}_fetchone"
    declaration = f"def {function_name}(\n{tab}{argument_string}\n) -> {return_type_string}:"
    return declaration


def get_python_list_of_tuples_for_list_of_dataclasses(
    postgres_function_arg: PostgresFunctionArgument,
) -> str:
    function_argname = (
        get_python_function_argument_name_for_postgres_function_argument_name(
            postgres_function_arg.argument_name
        )
    )
    return f"[astuple(x) for x in {function_argname}]"


def get_python_tuple_for_dataclass(
    postgres_function_arg: PostgresFunctionArgument,
) -> str:
    function_argname = (
        get_python_function_argument_name_for_postgres_function_argument_name(
            postgres_function_arg.argument_name
        )
    )
    return f"astuple({function_argname})"


def get_python_db_inputs(
    postgres_function_args: list[PostgresFunctionArgument], base_indent: int
) -> str:
    lines: list[str] = []
    for postgres_function_arg in postgres_function_args:
        db_argument_name = postgres_function_arg.argument_name
        python_argument_name = get_python_function_argument_name_for_postgres_function_argument_name(
            postgres_function_arg.argument_name
        )
        postgres_argument_type = postgres_function_arg.argument_type
        python_base_type = get_python_type_for_base_type_of_postgres_type(
            postgres_argument_type
        )
        if python_base_type is not None:
            tuple_expression = python_argument_name
        elif "[]" in postgres_function_arg.argument_type:
            tuple_expression = (
                get_python_list_of_tuples_for_list_of_dataclasses(
                    postgres_function_arg
                )
            )
        else:
            tuple_expression = get_python_tuple_for_dataclass(
                postgres_function_arg
            )
        db_input_line = (
            f"{base_indent * tab}{db_argument_name} = {tuple_expression}"
        )
        lines.append(db_input_line)
    return "\n".join(lines)


def get_python_cursor_initialisation_for_postgres_function(
    postgres_function: PostgresFunction, base_indent: int
) -> str:
    python_return_type = get_python_type_for_postgres_type(
        postgres_function.function_return
    )
    return f"{base_indent * tab}with conn.cursor(row_factory=class_row({python_return_type})) as cur:"


def get_python_execution_for_postgres_function(
    postgres_function: PostgresFunction, is_cursor: bool, base_indent: int
) -> str:
    argument_placeholder_string = ", ".join(
        ["%s"] * len(postgres_function.function_args)
    )
    argument_names = [
        function_arg.argument_name
        for function_arg in postgres_function.function_args
    ]
    variable_assignment = "rows = " if is_cursor else ""
    executing_object = "cur" if is_cursor else "conn"
    argument_list_string = f"[{', '.join(argument_names)}]"
    execute_line = (
        f"{base_indent * tab}{variable_assignment}{executing_object}.execute("
    )
    select_line = f'{(base_indent + 1) * tab}"SELECT * FROM {postgres_function.function_name}({argument_placeholder_string})",'
    argument_line = f"{(base_indent + 1) * tab}{argument_list_string}"
    closing_bracket_lines = f"{base_indent * tab})"
    lines = [execute_line, select_line, argument_line, closing_bracket_lines]
    return "\n".join(lines)


def get_python_fetchone(base_indent: int) -> str:
    return f"{base_indent * tab}return rows.fetchone()"


def get_python_fetchall(base_indent: int) -> str:
    return f"{base_indent * tab}return rows.fetchall()"


def get_python_try(base_indent: int) -> str:
    return f"{base_indent * tab}try:"


def get_python_except(base_indent: int) -> str:
    except_line = f"{base_indent * tab}except:"
    rollback_line = f"{(base_indent + 1) * tab}conn.rollback()"
    raise_line = f"{(base_indent + 1) * tab}raise"
    return f"{except_line}\n{rollback_line}\n{raise_line}"


def get_python_commit(base_indent: int) -> str:
    return f"{base_indent * tab}conn.commit()"


def get_python_code_for_postgres_function(
    postgres_function: PostgresFunction, fetchall: bool
) -> str:
    python_function_declaration = (
        get_python_function_declaration_for_postgres_function(
            postgres_function, fetchall
        )
    )
    python_db_inputs = get_python_db_inputs(
        postgres_function.function_args, base_indent=1
    )
    python_try = get_python_try(base_indent=1)
    if postgres_function.function_return == "VOID":
        python_conn_execution = get_python_execution_for_postgres_function(
            postgres_function, is_cursor=False, base_indent=2
        )
        python_commit = get_python_commit(base_indent=2)
        python_execution = "\n".join([python_conn_execution, python_commit])
    else:
        python_cursor_initialisation = (
            get_python_cursor_initialisation_for_postgres_function(
                postgres_function, base_indent=2
            )
        )
        python_cursor_execution = get_python_execution_for_postgres_function(
            postgres_function, is_cursor=True, base_indent=3
        )
        if fetchall:
            python_result_fetching = get_python_fetchall(base_indent=3)
        else:
            python_result_fetching = get_python_fetchone(base_indent=3)
        python_commit = get_python_commit(base_indent=3)
        python_execution = "\n".join(
            [
                python_cursor_initialisation,
                python_cursor_execution,
                python_commit,
                python_result_fetching,
            ]
        )
    python_except = get_python_except(base_indent=1)
    return "\n".join(
        [
            line
            for line in [
                python_function_declaration,
                python_db_inputs,
                python_try,
                python_execution,
                python_except,
            ]
            if line != ""
        ]
    )


def get_import_for_postgres_type(
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    import_dict: dict[str, list[str]],
    postgres_type_name: str,
) -> dict[str, list[str]]:
    python_type_name = get_python_type_for_postgres_type(postgres_type_name)
    if "list[" in python_type_name:
        python_type_name = python_type_name[5:-1]
    type_module = python_postgres_module_lookup.get(python_type_name)
    if type_module is not None:
        type_module_types_used = import_dict.get(type_module)
        if type_module_types_used is None:
            import_dict[type_module] = [python_type_name]
        if python_type_name not in import_dict[type_module]:
            import_dict[type_module].append(python_type_name)
    return import_dict


def get_imports_for_postgres_function_file(
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    postgres_functions: list[PostgresFunction],
) -> str:
    psycopg_imports = [
        "from dataclasses import astuple",
        "from typing import Optional",
        "from psycopg import Connection",
        "from psycopg.rows import class_row",
    ]
    psycopg_imports_string = "\n".join(psycopg_imports)
    import_dict: dict[str, list[str]] = {}
    for postgres_function in postgres_functions:
        import_dict = get_import_for_postgres_type(
            python_postgres_module_lookup,
            import_dict,
            postgres_function.function_return,
        )
        for function_arg in postgres_function.function_args:
            import_dict = get_import_for_postgres_type(
                python_postgres_module_lookup,
                import_dict,
                function_arg.argument_type,
            )
    import_statements: list[str] = []
    for import_module in import_dict.keys():
        imported_types = import_dict[import_module]
        imported_types_alphabetised = sorted(imported_types)
        import_types_string = f"from {import_module} import (\n"
        for imported_type in imported_types_alphabetised:
            import_types_string = (
                f"{import_types_string}{tab}{imported_type},\n"
            )
        import_types_string = f"{import_types_string})"
        import_statements.append(import_types_string)
    import_statement_string = "\n".join(import_statements)
    if import_statement_string == "":
        return psycopg_imports_string
    return "\n\n".join([psycopg_imports_string, import_statement_string])


def get_python_code_for_postgres_functions(
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    postgres_functions: list[PostgresFunction],
) -> str:
    python_sections = [
        get_imports_for_postgres_function_file(
            python_postgres_module_lookup, postgres_functions
        )
    ]
    for postgres_function in postgres_functions:
        if postgres_function.function_return != "VOID":
            fetchall_function = get_python_code_for_postgres_function(
                postgres_function, fetchall=True
            )
            python_sections.append(fetchall_function)
        fetchone_function = get_python_code_for_postgres_function(
            postgres_function, fetchall=False
        )
        python_sections.append(fetchone_function)
    return "\n\n\n".join(python_sections)


def get_postgres_functions_for_postgres_function_file(
    file_path: Path,
) -> list[PostgresFunction]:
    statements = get_statements_from_postgres_file(file_path, delimiter="$$;")
    return [
        postgres_function
        for statement in statements
        if (
            postgres_function := get_postgres_function_from_statement(statement)
        )
        is not None
    ]


def get_python_postgres_module_for_postgres_function_file(
    postgres_input_root_path: Path,
    python_output_root_module: str,
    python_postgres_module_lookup: PythonPostgresModuleLookup,
    file_path: Path,
) -> tuple[PythonPostgresModuleLookup, PythonPostgresModule[PostgresFunction]]:
    return get_postgres_module_for_postgres_file(
        get_postgres_functions_for_postgres_function_file,
        get_python_code_for_postgres_functions,
        postgres_input_root_path,
        python_output_root_module,
        python_postgres_module_lookup,
        file_path,
    )


if __name__ == "__main__":
    postgres_root_path = Path(sys.argv[1])
    python_output_module = sys.argv[2]
    input_script_file = Path(sys.argv[3])
    _, module = get_python_postgres_module_for_postgres_function_file(
        postgres_root_path, python_output_module, {}, input_script_file
    )
    print(module.python_code)
