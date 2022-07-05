import sys

from datetime import date
from api import authenticate
from record import add_to_logfile
from network import setup_network
from structs.service import make_services

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python " + sys.argv[0] + " <output>")
        exit(1)

    output_file = sys.argv[1]

    setup_network()
    creds = authenticate()

    uid = input("Service uid: ")

    services = make_services(uid, date.today(), creds)

    # add_to_logfile(output_file, creds)
