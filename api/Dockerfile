FROM python:3.13-bookworm AS builder

ARG POETRY_VERSION

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry==${POETRY_VERSION}

WORKDIR /app

COPY api/pyproject.toml api/poetry.lock ./

RUN touch README.md
RUN poetry install --without dev --no-root && rm -rf ${POETRY_CACHE_DIR}

FROM georgejkaye/postgres-codegen:latest AS codegen

WORKDIR /app

COPY db/code code

RUN poetry run python src/postgrescodegen/main.py code output api.db

FROM python:3.13-slim-bookworm AS runtime

RUN apt update
RUN apt install curl libpq-dev firefox-esr -y

RUN curl -L -o geckodriver.tar.gz --fail https://github.com/mozilla/geckodriver/releases/download/v0.37.1/geckodriver-v0.37.1-linux64.tar.gz/
RUN tar -zxvf geckodriver.tar.gz
RUN mv geckodriver /usr/bin
RUN chown root:root /usr/bin/geckodriver
RUN chmod +x /usr/bin/geckodriver

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    API_PORT=8000

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder /app/pyproject.toml ./app/pyproject.toml

ENV PYTHONPATH=/app/src

WORKDIR /app

COPY api/src src
COPY --from=codegen /app/output/db src/api/db

ENTRYPOINT ["python", "src/api/api/main.py"]
