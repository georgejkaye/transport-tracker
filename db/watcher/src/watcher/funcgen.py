import re

from watcher.classes import PostgresFunction, PostgresFunctionArgument

postgres_function_regex = r"CREATE(?: OR REPLACE)? FUNCTION ([A-z_]*)(?: )?\((.*)\).*RETURNS(?: SETOF)? (.*?) "

def get_postgres_function_from_postgres_code_str(
    postgres_function_code: str,
) -> Optional[PostgresFunction]:
    one_line_code = " ".join(postgres_function_code.replace("\n", " ").split())
    function_matches = re.match(postgres_function_regex, one_line_code)
    if function_matches is None:
        return None
    function_name = function_matches.group(1)
    function_args = function_matches.group(2)
    function_return = function_matches.group(3)

    code_open_bracket_split = one_line_code.split("(", 1)
    function_declaration = code_open_bracket_split[0]
    function_name = function_declaration.split("FUNCTION")[1].strip()
    code_close_bracket_split = code_open_bracket_split[1].split(")", 1)
    function_args = code_close_bracket_split[0]
    function_arg_split = function_args.split(",")
    postgres_function_args: list[PostgresFunctionArgument] = []
    for function_arg in function_arg_split:
        function_arg_split = function_arg.split()
        function_arg_name = function_arg_split[0]
        function_arg_type = function_arg_split[1]
        postgres_function_arg = PostgresFunctionArgument(
            function_arg_name, function_arg_type
        )
        postgres_function_args.append(postgres_function_arg)
    code_language_split =

    return PostgresFunction(
        function_name, function_return, postgres_function_args
    )
