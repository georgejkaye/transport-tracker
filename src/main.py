from api import authenticate
from input import record_new_journey
from network import setup_network

setup_network()
authenticate()
record_new_journey()
