# transport-tracker

A full stack web app for tracking use of public transport.

## Development

### Environment

- `POETRY_VERSION`
- `API_PORT`
- `CLIENT_PORT`
- `RTT_USER`

For populating the dev database we pull data from the prod database using the
following variables.

- `DB_NAME`
- `DB_USER`
- `DB_HOST`

### Secrets

- `rtt.secret` Realtime Trains API key
- `db.secret` Prod database password

### Docker

```sh
docker compose -f docker-compose.dev.yml up --build
```
