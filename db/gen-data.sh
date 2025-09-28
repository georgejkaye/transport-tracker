#!/bin/sh

PASSWORD=$(cat /run/secrets/db_secret)

DB_POPULATE_DIR=/db/.populate

if [ ! -d $DB_POPULATE_DIR ]
then
    mkdir $DB_POPULATE_DIR
fi

DATA_FILE="$DB_POPULATE_DIR/0_dump.pgdata"

for EXISTING_SCRIPT in `find $DB_POPULATE_DIR -name *sql`
do
    if [ "$EXISTING_SCRIPT" != "$DATA_FILE" ]
    then
        rm $EXISTING_SCRIPT
    fi
done

if [ -f "$DATA_FILE" ] && [ -s "$DATA_FILE" ]
then
    echo "Data dump $DATA_FILE already exists, skipping data generation"
else
    echo "Dumping db from $DB_NAME@$DB_HOST as user $DB_USER... (this may take a while)"

    PGPASSWORD=$PASSWORD pg_dump \
        -h $DB_HOST \
        -d $DB_NAME \
        -U $DB_USER \
        --no-owner \
        --no-privileges \
        --no-acl \
        --format custom \
        --file $DATA_FILE
fi

DB_DATA_DIR="/db/data"

for DATA_FILE in `find $DB_DATA_DIR -name *sql`
do
    cp $DATA_FILE "$DB_POPULATE_DIR/1_data_${DATA_FILE#$DB_DATA_DIR/}"
done

DB_CODE_DIR="/db/code"

for CODE_FILE in `find $DB_CODE_DIR -name *sql`
do
    FILE_NAME="2_code_${CODE_FILE#$DB_CODE_DIR/}"
    echo "file name is $FILE_NAME"
    OUTPUT_FILE=$( echo $FILE_NAME | sed 's/\//_/g' )
    echo "output is $OUTPUT_FILE"
    cp $CODE_FILE "$DB_POPULATE_DIR/$OUTPUT_FILE"
done

