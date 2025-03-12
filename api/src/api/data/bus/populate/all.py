import sys

from api.data.bus.populate.operators import populate_bus_operators
from api.data.bus.populate.service import populate_bus_services
from api.data.bus.populate.stop import populate_bus_stops
from api.data.bus.populate.vehicle import populate_bus_vehicles
from api.utils.database import connect

with connect(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]) as (conn, _):
    populate_bus_stops(conn, sys.argv[5])
    operators = populate_bus_operators(conn, sys.argv[6])
    operator_nocs = set()
    for operator in operators:
        operator_nocs.add(operator.national_code)
    populate_bus_services(conn, operator_nocs, sys.argv[7])
    populate_bus_vehicles(conn)
