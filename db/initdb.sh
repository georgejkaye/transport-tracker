echo "Initialising db..."

PGPASSWORD=$POSTGRES_PASSWORD pg_restore \
    --no-privileges \
    --no-owner \
    --no-acl \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    --single-transaction < /docker-entrypoint-initdb.d/dump.pgdata