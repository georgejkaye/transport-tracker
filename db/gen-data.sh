#!/bin/sh

PASSWORD=$(cat /run/secrets/db_secret)

DB_POPULATE_DIR=/db/.populate

if [ ! -d $DB_POPULATE_DIR ]
then
    mkdir $DB_POPULATE_DIR
fi

DATA_FILE="$DB_POPULATE_DIR/dump.pgdata"

for EXISTING_SCRIPT in `find $DB_POPULATE_DIR -name *sql`
do
    if [ "$EXISTING_SCRIPT" != "$DATA_FILE" ]
    then
        rm $EXISTING_SCRIPT
    fi
done

cp /db/extensions.sql "$DB_POPULATE_DIR/0_extensions.sql"

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

cp /db/initdb.sh "$DB_POPULATE_DIR/1_init.sh"

DB_DATA_DIR="/db/data"

for DATA_FILE in `find $DB_DATA_DIR -name *sql`
do
    cp $DATA_FILE "$DB_POPULATE_DIR/2_data_${DATA_FILE#$DB_DATA_DIR/}"
done

DB_CODE_DIR="/db/code"

for CODE_FILE in `find $DB_CODE_DIR -name *sql`
do
    FILE_NAME="3_code_${CODE_FILE#$DB_CODE_DIR/}"
    OUTPUT_FILE=$( echo $FILE_NAME | sed 's/\//_/g' )
    cp $CODE_FILE "$DB_POPULATE_DIR/$OUTPUT_FILE"
done

