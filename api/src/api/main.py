from api.data.database import connect, disconnect
from api.record import add_to_logfile

if __name__ == "__main__":
    (conn, cur) = connect()
    add_to_logfile(conn, cur)
    disconnect(conn, cur)
