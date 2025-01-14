#!/bin/sh

PASSWORD=$(cat /run/secrets/db_secret)

PGPASSWORD=$PASSWORD pg_dump --column-inserts --data-only \
    --table=operatorcode \
    --table=operator \
    --table=brand \
    --table=stock \
    --table=stocksubclass \
    --table=stockformation \
    --table=operatorstock \
    --table=station \
    --table=stationpoint \
    --table=service \
    --table=serviceendpoint \
    --table=call \
    --table=associatedservice \
    --table=leg \
    --table=legcall \
    --table=stocksegment \
    --table=stockreport \
    --table=stocksegmentreport \
    -h $DB_HOST \
    -d $DB_NAME \
    -U $DB_USER > /db/scripts/99_populate.sql


