import sys

from train_tracker.api import authenticate
from train_tracker.record import add_to_logfile
from train_tracker.network import setup_network

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python " + sys.argv[0] + " <output>")
        exit(1)

    output_file = sys.argv[1]

    setup_network()
    creds = authenticate()
    add_to_logfile(output_file, creds)