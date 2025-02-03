from api.utils.database import connect
from api.record.record import add_to_logfile

if __name__ == "__main__":
    with connect() as (conn, cur):
        add_to_logfile(conn, cur)
