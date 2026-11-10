source ./.env

roll_script() {
    file=$1
    echo "Rolling in $file..."
    echo
    psql -P pager=off -h $DB_HOST -d $DB_NAME -U $DB_USER -f $file
    echo
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

