DB_HOST=$1
DB_NAME=$2
DB_USER=$3

DB_DIR=$( dirname $0 )
SCRIPTS_DIR="$DB_DIR/scripts"
SCRIPTS=$( find $SCRIPTS_DIR | sort | grep sql | grep -v schema )

rm output.log

for SCRIPT_FILE in $SCRIPTS;
do
    psql -h $DB_HOST -d $DB_NAME -U $DB_USER -f $SCRIPT_FILE -q 2&>> output.log
done

ERROR_OUTPUT=0

cat output.log | while read line;
do
    if [[ $line != *"psql"* && $ERROR_OUTPUT == 0 ]];
    then
        continue
    fi

    if [[ $line == *"NOTICE"* ]];
    then
        ERROR_OUTPUT=0
        continue
    fi

    ERROR_OUTPUT=1

    echo $line
done