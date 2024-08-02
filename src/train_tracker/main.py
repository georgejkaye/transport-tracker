from train_tracker.data.database import connect, disconnect
from train_tracker.record import add_to_logfile

if __name__ == "__main__":
    (conn, cur) = connect()
    add_to_logfile(conn, cur)
    disconnect(conn, cur)
