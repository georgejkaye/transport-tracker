#!/bin/sh

PROD_COMPOSE=docker-compose.prod.yml
CI_COMPOSE=docker-compose.ci.yml

SERVICES=$( \
    docker compose \
        -f $PROD_COMPOSE \
        -f $CI_COMPOSE \
        config \
        --services
)

echo "Printing container logs for:"
echo
echo "$SERVICES"
echo

for SERVICE in $SERVICES; do
    echo "==================="
    echo
    echo "Logs for service $SERVICE"
    echo
    docker compose \
        -f $PROD_COMPOSE \
        -f $CI_COMPOSE \
        logs \
        --no-log-prefix \
        $SERVICE
    echo
done
