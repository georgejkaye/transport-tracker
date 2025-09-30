# Build image
FROM python:3.13-bookworm AS builder

RUN apt install postgresql-client

ARG POETRY_VERSION
RUN pip install poetry==${POETRY_VERSION}

WORKDIR /app
COPY pyproject.toml poetry.lock mypy.ini ./
# Poetry complains without a readme
RUN touch README.md
RUN poetry install --no-root

COPY src ./src
RUN poetry install

RUN mkdir /run/secrets
RUN echo "transport" > /run/secrets/db_secret

ENTRYPOINT ["poetry", "run", "python", "src/api/api/main.py"]
