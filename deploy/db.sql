#!/bin/bash

source ./.env

roll_script() {
    file=$1
    echo "Rolling in $file..."
    echo
    psql -v ON_ERROR_STOP=1 -P pager=off -h $DB_HOST -d $DB_NAME -U $DB_USER -f $file
    echo

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
	
roll_scripts_in_directory db/data

roll_scripts_in_directory db/code/domains
roll_scripts_in_directory db/code/types
roll_scripts_in_directory db/code/views
roll_scripts_in_directory db/code/functions

