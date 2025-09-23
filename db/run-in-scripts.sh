DB_HOST=$1
DB_NAME=$2
DB_USER=$3

DB_DIR=$( dirname $0 )
SCRIPTS_DIR="$DB_DIR/scripts"
SCRIPTS=$( find $SCRIPTS_DIR | sort | grep sql | grep -v schema )

for SCRIPT_FILE in $SCRIPTS;
do
    psql -h $DB_HOST -d $DB_NAME -U $DB_USER -a -f $SCRIPT_FILE
done