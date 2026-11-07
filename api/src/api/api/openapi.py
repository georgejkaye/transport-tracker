import json
import sys

from fastapi.openapi.utils import get_openapi

from api.api.app import app
from api.utils.environment import get_mandatory_env_variable


def generate_openapi_file(openapi_json_file: str):
    openapi = get_openapi(
        title="Transport tracker",
        version=get_mandatory_env_variable("VERSION"),
        routes=app.routes,
    )
    print(openapi)
    with open(openapi_json_file, "w") as f:
        json.dump(openapi, f)


if __name__ == "__main__":
    generate_openapi_file(sys.argv[1])
