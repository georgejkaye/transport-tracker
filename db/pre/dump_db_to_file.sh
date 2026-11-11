#!/bin/sh

DATA_FILE=$1
PASSWORD=$(cat $DB_PASSWORD_SECRET_FILE)

if [ -f "$DATA_FILE" ] && [ -s "$DATA_FILE" ]
then
    echo "Data dump $DATA_FILE already exists, skipping data generation"
else
    echo "Dumping db from $DB_NAME@$DB_HOST as user $DB_USER... (this may take a while)"

    TABLES=$(
        PGPASSWORD=$PASSWORD \
        psql \
            -h $DB_HOST \
            -p $DB_PORT \
            -d $DB_NAME \
            -U $DB_USER \
            --tuples-only \
            -c \
                "SELECT CONCAT(table_schema, '.', table_name)
                FROM information_schema.tables
                WHERE table_type='BASE TABLE' AND table_schema IN ('public','auth');" \
        | xargs -I{} echo -n " -t {}"
    )

    PGPASSWORD=$PASSWORD pg_dump \
        -h $DB_HOST \
        -p $DB_PORT \
        -d $DB_NAME \
        -U $DB_USER \
        --no-owner \
        --no-privileges \
        --no-acl \
        --format custom \
        --file $DATA_FILE \
        $TABLES

fi

