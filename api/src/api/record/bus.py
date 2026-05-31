from datetime import datetime, timedelta
from typing import Optional

from api.data.bus.leg import BusLegIn, insert_leg
from api.data.bus.operators import (
    BusOperatorDetails,
)
from api.data.bus.pages.journey.classes import BustimesJourney
from api.data.bus.pages.journey.reader import get_bustimes_journey
from api.data.bus.stop import (
    BusStopDeparture,
    BusStopDetails,
    get_bus_stops,
    get_departures_from_bus_stop,
    short_string_of_bus_stop,
    short_string_of_bus_stop_departure,
)
from api.data.bus.trip import (
    BusCallIn,
    BusJourneyDetails,
    BusJourneyIn,
    get_bus_trip,
    string_of_bus_call_in,
)
from api.data.bus.vehicle import (
    BusVehicleDetails,
    get_bus_vehicles_by_id,
    get_bus_vehicles_by_operator_and_id,
    string_of_bus_vehicle_out,
)
from api.data.selenium.driver import SeleniumDriver
from api.user import User, input_user
from api.utils.database import connect, get_db_connection_data_from_args
from api.utils.interactive import (
    PickSingle,
    information,
    input_day,
    input_month,
    input_select,
    input_select_paginate,
    input_text,
    input_time,
    input_year,
)
from psycopg import Connection


def get_bus_stop_input(
    conn: Connection, prompt: str = "Bus stop name"
) -> Optional[BusStopDetails]:
    search_string = input_text("Bus stop name")
    if search_string is None:
        return None
    bus_stops = get_bus_stops(conn, search_string)
    bus_stop_choice = input_select_paginate(
        "Select bus stop", bus_stops, display=short_string_of_bus_stop
    )
    match bus_stop_choice:
        case PickSingle(bus_stop):
            return bus_stop
        case _:
            return None


def get_bus_stop_departure_input(
    departures: list[BusStopDeparture],
) -> Optional[BusStopDeparture]:
    departure_choice = input_select_paginate(
        "Select departure",
        departures,
        display=short_string_of_bus_stop_departure,
    )
    match departure_choice:
        case PickSingle(departure):
            return departure
        case _:
            return None


def get_alight_stop_input(
    calls: list[BusCallIn], board_call_index: int
) -> Optional[tuple[BusCallIn, int]]:
    possible_alight_calls = calls[board_call_index + 1 :]
    alight_choice = input_select_paginate(
        "Alight call",
        list(enumerate(possible_alight_calls)),
        lambda x: string_of_bus_call_in(x[1]),
    )
    match alight_choice:
        case PickSingle((i, choice)):
            return (choice, i + board_call_index + 1)
        case _:
            return None


def input_vehicle(
    vehicles: list[BusVehicleDetails],
) -> Optional[BusVehicleDetails]:
    result = input_select("Select vehicle", vehicles, string_of_bus_vehicle_out)
    match result:
        case PickSingle(vehicle):
            return vehicle
        case _:
            return None


def get_bus_vehicle(
    conn: Connection, bus_operator: BusOperatorDetails
) -> Optional[BusVehicleDetails]:
    vehicle_id = input_text("Vehicle id")
    if vehicle_id is None:
        return None
    vehicles = get_bus_vehicles_by_operator_and_id(conn, bus_operator, vehicle_id)
    if len(vehicles) == 1:
        return vehicles[0]
    if len(vehicles) > 1:
        vehicle = input_vehicle(vehicles)
        if vehicle is not None:
            return vehicle
    information(
        f"Vehicle {vehicle_id} not found for operator {bus_operator.name}, falling back to all operators"
    )
    vehicles = get_bus_vehicles_by_id(conn, vehicle_id)
    if len(vehicles) == 0:
        information(f"No vehicles found with id {vehicle_id}")
        return None
    return input_vehicle(vehicles)


def get_board_call_index_from_bustimes_journey(
    journey: BustimesJourney, board_atco: str
) -> Optional[int]:
    for i, call in enumerate(journey.calls):
        if call.stop_id == board_atco:
            return i
    return None


def get_bus_leg_input(
    conn: Connection, users: list[User]
) -> Optional[BusJourneyDetails]:
    board_stop = get_bus_stop_input(conn, prompt="Board stop")
    if board_stop is None:
        print("Could not get board stop")
        exit(-1)

    board_year = input_year()
    if board_year is None:
        return None

    board_month = input_month()
    if board_month is None:
        return None

    board_day = input_day(board_month, board_year)
    if board_day is None:
        return None

    board_time = input_time()
    if board_time is None:
        return None

    board_datetime = datetime(
        board_year, board_month, board_day, board_time.hour, board_time.minute
    )

    today = datetime.today()

    if board_datetime.date() < today.date() - timedelta(days=28):
        board_day_of_week = board_datetime.weekday()
        today_day_of_week = today.weekday()
        day_of_week_diff = board_day_of_week - today_day_of_week
        if day_of_week_diff < 0:
            day_of_week_diff = day_of_week_diff + 7
        new_board_date = today.date() + timedelta(days=day_of_week_diff)

        new_board_datetime = datetime.combine(new_board_date, board_datetime.time())
        information(
            f"{board_datetime.strftime('%d/%m/%Y %H:%M:%S')} is 28 days before today, "
            + f"using {new_board_datetime.strftime('%d/%m/%Y %H:%M:%S')} instead"
        )
        datetime_offset = new_board_datetime - board_datetime
        board_datetime = new_board_datetime
    else:
        datetime_offset = timedelta(0)

    departures = get_departures_from_bus_stop(
        board_stop, board_datetime, datetime_offset
    )
    if len(departures) == 0:
        information("No departures from bus stop")
        return None

    departure = get_bus_stop_departure_input(departures)
    if departure is None:
        return None

    if departure.live:
        journey = get_bustimes_journey(
            SeleniumDriver(),
            departure.dep_time.date(),
            board_stop.atco,
            departure.bustimes_id,
        )
        if journey is None:
            print(f"Could not get journey {departure.bustimes_id}")
            return None
        board_call_index = get_board_call_index_from_bustimes_journey(
            journey, board_stop.atco
        )
        if board_call_index is None:
            print("Could not get board index")
            return None
        journey_calls = [
            BusCallIn(
                i,
                call.stop_id,
                call.stop_name,
                call.plan_arr,
                call.act_arr,
                call.plan_dep,
                call.act_dep,
            )
            for i, call in enumerate(journey.calls)
        ]
        trip_id = journey.trip_id
    else:
        journey = None
        trip_id = departure.bustimes_id
        journey_calls = []
    trip_and_board_call_index = get_bus_trip(
        conn,
        trip_id,
        board_stop,
        departure,
    )
    if trip_and_board_call_index is None:
        print(f"Could not get trip {trip_id}")
        return None
    (journey_timetable, board_call_index) = trip_and_board_call_index
    if journey is None:
        journey_calls = journey_timetable.calls

    alight_call_and_index = get_alight_stop_input(journey_calls, board_call_index)
    if alight_call_and_index is None:
        return None

    (_, alight_call_index) = alight_call_and_index

    if journey is None or journey.vehicle is None or journey.vehicle.identifier is None:
        vehicle = get_bus_vehicle(conn, journey_timetable.operator)
    else:
        vehicle_options = get_bus_vehicles_by_operator_and_id(
            conn, journey_timetable.operator, journey.vehicle.identifier
        )
        if len(vehicle_options) == 0:
            information(
                f"Could not find vehicle {journey.vehicle.identifier} for {journey_timetable.operator.name}, skipping"
            )
            vehicle = None
        else:
            vehicle = vehicle_options[0]

    journey = BusJourneyIn(
        journey_timetable.id,
        journey_timetable.operator,
        journey_timetable.service,
        journey_calls,
        vehicle,
    )
    leg = BusLegIn(journey, board_call_index, alight_call_index)
    insert_leg(conn, users, leg)


if __name__ == "__main__":
    connection_data = get_db_connection_data_from_args()
    with connect(connection_data) as conn:
        users = input_user(conn)
        if users is not None:
            get_bus_leg_input(conn, users)
