import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def get_env_variable(key: str) -> Optional[str]:
    val = os.environ.get(key)
    return val


def get_secret_file_contents(file: str) -> str:
    with open(file, "r") as f:
        return f.readline().rstrip()


def get_secret(key: str) -> Optional[str]:
    file = get_env_variable(key)
    if file is not None and os.path.exists(file):
        return get_secret_file_contents(file)
    return None
