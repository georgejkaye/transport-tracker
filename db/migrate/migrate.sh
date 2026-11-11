#!/bin/bash

PASSWORD=$(cat $DB_PASSWORD_SECRET_FILE)

roll_script() {
    file=$1
    echo "Rolling in $file..."
    PGPASSWORD=$PASSWORD psql -v ON_ERROR_STOP=1 -P pager=off -h $DB_HOST -d $DB_NAME -U $DB_USER -f $file

    if [[ $? -ne 0 ]]; then
        echo "Failed to roll in script $file"
        exit 1
    fi
}

roll_scripts_in_directory() {
    directory=$1
    for file in $(find $directory -name *sql); do
        roll_script $file
    done
}

roll_scripts_in_directory data

roll_scripts_in_directory code/domains
roll_scripts_in_directory code/types
roll_scripts_in_directory code/views
roll_scripts_in_directory code/functions

