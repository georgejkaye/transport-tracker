# Train journey recorder

Get the details of trains you've been on, and present them prettily

## Database

You will need a Postgres database with the schema specified in the
`src/train_tracker/init.sql` file.
This can be set up with the following command after creating an
appropriately named database:

```sh
psql -h <database host> -d <database name> -U <database user> < src/train_tracker/init.sql
```

## Credentials

You will need a Realtime Trains API username and password, which can be found at the [Realtime Trains API page](https://api.rtt.io/) after signing up.

## Environment

- `RTT_USER`
- `DATA_DIR` location to store downloaded data files (default `data`)
- `DB_NAME`
- `DB_USER`
- `DB_HOST`

The following environment variables should specify the location of files
containing appropriate secrets.

- `RTT_PASSWORD`
- `DB_PASSWORD`

The `.env.blank` file also specifies the required variables.

## Dependencies

Project dependencies are managed by [Poetry](https://python-poetry.org/).
Once you have it installed, run the following command to install all
dependencies in a virtual environment.

```sh
poetry install
```

## Running

To run the interactive leg recording script, run the following:

```sh
poetry run python src/train_tracker/main.py
```
