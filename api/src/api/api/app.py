from fastapi import FastAPI

from api.api.lifespan import lifespan
from api.api.routers.train import train
from api.api.routers.users import user
from api.api.routers.utils import utils
from api.utils.environment import get_mandatory_env_variable

app = FastAPI(
    title="Train tracker API",
    summary="API for interacting with the train tracker",
    version=get_mandatory_env_variable("VERSION"),
    contact={
        "name": "George Kaye",
        "email": "georgejkaye@gmail.com",
        "url": "https://georgejkaye.com",
    },
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.en.html",
    },
    lifespan=lifespan,
)


@app.get("/hc", summary="Healthcheck", tags=["debug"])
async def get_healthcheck() -> str:
    return "Hello!"


app.include_router(train.router)
app.include_router(user.router)
app.include_router(utils.router)
