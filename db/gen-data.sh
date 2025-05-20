#!/bin/sh

PASSWORD=$(cat /run/secrets/db_secret)

DATA_FILE=/db/scripts/dump.pgdata

if [ -f $DATA_FILE ]; then
    echo "Data dump $DATA_FILE already exists, skipping data generation"
else
    echo "Dumping data from $DB_NAME@$DB_HOST as user $DB_USER... (this may take a while)"

    PGPASSWORD=$PASSWORD pg_dump \
        -h $DB_HOST \
        -d $DB_NAME \
        -U $DB_USER \
        --no-owner \
        --no-privileges \
        --no-acl \
        --format custom \
        --file $DATA_FILE \
        --column-inserts \
        --data-only \
        --table=traveller \
        --table=operatorcode \
        --table=operator \
        --table=brand \
        --table=stock \
        --table=stocksubclass \
        --table=stockformation \
        --table=operatorstock \
        --table=station \
        --table=stationname \
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
        --table=busstop \
        --table=busoperator \
        --table=busservice \
        --table=busservicevia \
        --table=busjourney \
        --table=buscall \
        --table=busmodel \
        --table=busvehicle \
        --table=busleg
fi