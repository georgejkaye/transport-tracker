import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def get_env_variable(key: str) -> Optional[str]:
    val = os.environ.get(key)
    return val


def get_secret(key: str) -> Optional[str]:
    file = get_env_variable(key)
    if file is not None and os.path.exists(file):
        with open(file, "r") as f:
            val = f.readline().rstrip()
        return val
    return None
