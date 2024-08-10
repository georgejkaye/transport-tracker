#!/bin/sh

PASSWORD=$(cat /run/secrets/db_secret)

PGPASSWORD=$PASSWORD pg_dump --column-inserts --data-only \
    --table=operator \
    --table=brand \
    --table=stock \
    --table=stocksubclass \
    --table=stockformation \
    --table=operatorstock \
    --table=station \
    -h $DB_HOST \
    -d $DB_NAME \
    -U $DB_USER > /db/scripts/populate.sql
