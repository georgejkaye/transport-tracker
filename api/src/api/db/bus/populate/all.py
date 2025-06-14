import sys

from api.db.bus.populate.operators import populate_bus_operators
from api.db.bus.populate.service import populate_bus_services
from api.db.bus.populate.stop import populate_bus_stops
from api.db.bus.populate.vehicle import populate_bus_vehicles
from api.utils.database import connect, get_db_connection_data_from_args

connection_data = get_db_connection_data_from_args()

with connect(connection_data) as conn:
    populate_bus_stops(conn, sys.argv[5])
    operators = populate_bus_operators(conn, sys.argv[6])
    operator_nocs: set[str] = set()
    for operator in operators:
        operator_nocs.add(operator.national_code)
    populate_bus_services(conn, operator_nocs, sys.argv[7])
    populate_bus_vehicles(conn)
