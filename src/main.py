import sys

from api import authenticate
from record import record_new_journey
from network import setup_network

if len(sys.argv) != 2:
    print("Usage: python " + sys.argv[0] + " <output>")
    exit(1)

output_file = sys.argv[1]

setup_network()
authenticate()
record_new_journey(output_file)
