from dataclasses import dataclass

from api.utils.environment import get_env_variable, get_secret


@dataclass
class Credentials:
    user: str
    password: str


def get_api_credentials(prefix: str) -> Credentials:
    user = get_env_variable(f"{prefix}_USER")
    password = get_secret(f"{prefix}_PASSWORD")
    if user is not None and password is not None:
        return Credentials(user, password)
    else:
        raise RuntimeError(f"Invalid {prefix} user and password")
