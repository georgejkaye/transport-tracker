#!/bin/sh

DB_DOCKER_VOLUME=/volume

if [ ! -d $DB_DOCKER_VOLUME ]
then
    mkdir $DB_DOCKER_VOLUME
fi

cp /extensions.sql "$DB_DOCKER_VOLUME/0_extensions.sql"
./dump_db_to_file.sh "$DB_DOCKER_VOLUME/dump.pgdata"
cp /restore_db_from_dump.sh "$DB_DOCKER_VOLUME/1_restore_db_from_dump.sh"
