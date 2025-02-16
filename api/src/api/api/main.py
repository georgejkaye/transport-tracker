import uvicorn

from fastapi import FastAPI

from api.utils.environment import get_env_variable
from api.api.routers.train import train


app = FastAPI(
    title="Train tracker API",
    summary="API for interacting with the train tracker",
    version="1.0.0",
    contact={
        "name": "George Kaye",
        "email": "georgejkaye@gmail.com",
        "url": "https://georgejkaye.com",
    },
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.en.html",
    },
)

app.include_router(train.router)


def start():
    if get_env_variable("API_ENV") == "prod":
        reload = False
    elif get_env_variable("API_ENV") == "dev":
        reload = True
    else:
        raise RuntimeError("API_ENV not set")
    port_var = get_env_variable("API_PORT")
    if port_var is None:
        port = 8000
    elif not port_var.isnumeric():
        raise RuntimeError(f"API_PORT must be number but it is {port_var}")
    else:
        port = int(port_var)
    uvicorn.run(
        "api.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    start()
