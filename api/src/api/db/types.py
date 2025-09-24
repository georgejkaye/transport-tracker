from psycopg import Connection

from api.classes.bus.journey import (
    register_bus_call_details,
    register_bus_call_stop_details,
    register_bus_journey_call_details,
    register_bus_journey_details,
    register_bus_journey_service_details,
)
from api.classes.bus.leg import (
    register_bus_leg_service_details,
    register_bus_leg_user_details,
)
from api.classes.bus.operators import (
    register_bus_operator_details,
)
from api.classes.bus.overview import (
    register_bus_vehicle_leg_details,
    register_bus_vehicle_user_details,
)
from api.classes.bus.vehicle import register_bus_vehicle_details
from api.classes.train.legs import (
    register_train_leg_call_out_data,
    register_train_leg_call_point_out_data,
    register_train_leg_call_points_out_data,
    register_train_leg_operator_out_data,
    register_train_leg_out_data,
    register_train_leg_points_out_data,
    register_train_leg_service_out_data,
    register_train_leg_station_out_data,
    register_train_leg_stock_report_out_data,
    register_train_leg_stock_segment_out_data,
)
from api.classes.train.operators import (
    register_train_operator_details_out_data,
    register_train_operator_out_data,
)
from api.classes.train.station import (
    register_train_station_leg_points_out_data,
    register_train_station_point_out_data,
    register_train_station_points_out_data,
)
from api.classes.users.train.legs import (
    register_transport_user_train_leg_operator_out_data,
    register_transport_user_train_leg_out_data,
    register_transport_user_train_leg_station_out_data,
)
from api.db.bus.user.stop import register_bus_stop_leg_details


def register_types(conn: Connection):
    register_train_operator_out_data(conn)
    register_train_operator_details_out_data(conn)
    register_train_leg_operator_out_data(conn)
    register_train_leg_station_out_data(conn)
    register_train_leg_service_out_data(conn)
    register_train_leg_call_out_data(conn)
    register_train_leg_stock_report_out_data(conn)
    register_train_leg_stock_segment_out_data(conn)
    register_train_leg_out_data(conn)
    register_train_leg_call_point_out_data(conn)
    register_train_leg_call_points_out_data(conn)
    register_train_leg_points_out_data(conn)
    register_train_station_point_out_data(conn)
    register_train_station_points_out_data(conn)
    register_train_station_leg_points_out_data(conn)
    register_bus_operator_details(conn)
    register_bus_call_stop_details(conn)
    register_bus_call_details(conn)
    register_bus_journey_call_details(conn)
    register_bus_journey_service_details(conn)
    register_bus_journey_details(conn)
    register_bus_leg_service_details(conn)
    register_bus_vehicle_leg_details(conn)
    register_bus_vehicle_user_details(conn)
    register_bus_vehicle_details(conn)
    register_bus_leg_user_details(conn)
    register_bus_stop_leg_details(conn)
    register_transport_user_train_leg_station_out_data(conn)
    register_transport_user_train_leg_operator_out_data(conn)
    register_transport_user_train_leg_out_data(conn)
