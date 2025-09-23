from psycopg import Connection

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
    register_transport_user_train_leg_station_out_data(conn)
    register_transport_user_train_leg_operator_out_data(conn)
    register_transport_user_train_leg_out_data(conn)
