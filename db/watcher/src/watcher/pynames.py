def get_python_name_for_postgres_type_name(postgres_type_name: str) -> str:
    return "".join(
        x.capitalize() for x in postgres_type_name.lower().split("_")
    )


def get_python_name_for_postgres_function_name(
    postgres_function_name: str,
) -> str:
    return postgres_function_name.lower()
