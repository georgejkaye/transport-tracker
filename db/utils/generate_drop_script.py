import os
from pathlib import Path
import re

function_regex = r"CREATE(?: OR REPLACE)? FUNCTION (.*)(?: )?\("
type_regex = r"CREATE TYPE (.*) AS"


def write_drop_script(file: Path | str, regex: str, drop_expression: str) -> str:
    with open(file) as f:
        content = f.read()
    output: list[str] = []
    function_matches = re.findall(regex, content)
    for function_match in function_matches:
        output.append(f"{drop_expression} {function_match};")
    output_string = "\n".join(reversed(output))
    return output_string


def write_drop_function_script(file: Path | str) -> str:
    return write_drop_script(file, function_regex, "DROP FUNCTION")


def write_drop_type_script(file: Path | str) -> str:
    return write_drop_script(file, type_regex, "DROP TYPE")


def get_db_script_path(
    script_file_directory: Path, script_directory: str, file: str
) -> Path:
    return script_file_directory / ".." / "scripts" / script_directory / file


def write_all_drop_scripts() -> str:
    script_file_path = Path(os.path.realpath(__file__)).parent.resolve()
    drop_train_function_script = write_drop_function_script(
        get_db_script_path(script_file_path, "4_select", "1_train.sql")
    )
    drop_train_type_script = write_drop_type_script(
        get_db_script_path(script_file_path, "1_types", "1_train.sql")
    )
    return "\n\n".join([drop_train_function_script, drop_train_type_script])


if __name__ == "__main__":
    drop_scripts = write_all_drop_scripts()
    with open("drop.sql", "w+") as f:
        f.write(drop_scripts)
