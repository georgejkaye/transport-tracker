from datetime import datetime, timedelta
from typing import Any, Optional

from psycopg import Connection

from api.classes.train.station import (
    DbTrainStationOutData,
    TrainServiceAtStation,
    TrainStationIdentifiers,
)
from api.db.train.stations import select_station_by_name
from api.utils.credentials import get_api_credentials
from api.utils.request import make_get_request
from api.utils.times import get_datetime_route, make_timezone_aware

station_endpoint = "https://api.rtt.io/api/v1/json/search"


def get_services_at_station(
    conn: Connection, station: DbTrainStationOutData, dt: datetime
) -> list[TrainServiceAtStation]:
    endpoint = f"{station_endpoint}/{station.station_crs}/{get_datetime_route(dt, True)}"
    rtt_credentials = get_api_credentials("RTT")
    response = make_get_request(endpoint, rtt_credentials)
    if not response.status_code == 200:
        return []
    data = response.json()
    if data.get("services") is None:
        return []
    services: list[TrainServiceAtStation] = []
    for service in data["services"]:
        if service["serviceType"] == "train":
            services.append(response_to_service_at_station(conn, service))
    return services


def response_to_train_station_identifiers(
    conn: Connection, data: dict[str, Any]
) -> TrainStationIdentifiers:
    name = data["description"]
    station = select_station_by_name(conn, name)
    if station is None:
        print(f"No station with name {name} found. Please update the database.")
        exit(1)
    return TrainStationIdentifiers(station.station_crs.upper(), name)


def response_to_datetime(
    data: dict[str, Any], time_field: str, run_date: datetime
) -> Optional[datetime]:
    datetime_string = data.get(time_field)
    if datetime_string is not None:
        hours = int(datetime_string[0:2])
        minutes = int(datetime_string[2:4])
        next_day = data.get(f"{time_field}NextDay")
        if next_day is not None and next_day:
            actual_datetime = run_date + timedelta(
                days=1, hours=hours, minutes=minutes
            )
        else:
            actual_datetime = run_date + timedelta(
                days=0, hours=hours, minutes=minutes
            )
        return make_timezone_aware(actual_datetime)
    else:
        return None


def response_to_service_at_station(
    conn: Connection, data: dict[str, Any]
) -> TrainServiceAtStation:
    id: str = data["serviceUid"]
    headcode: str = data["trainIdentity"]
    operator_code: str = data["atocCode"]
    operator_name: str = data["atocName"]
    run_date = datetime.strptime(data["runDate"], "%Y-%m-%d")
    origins = [
        response_to_train_station_identifiers(conn, origin)
        for origin in data["locationDetail"]["origin"]
    ]
    destinations = [
        response_to_train_station_identifiers(conn, destination)
        for destination in data["locationDetail"]["destination"]
    ]
    plan_dep = response_to_datetime(
        data["locationDetail"], "gbttBookedDeparture", run_date
    )
    act_dep = response_to_datetime(
        data["locationDetail"], "realtimeDeparture", run_date
    )
    return TrainServiceAtStation(
        id,
        headcode,
        run_date,
        origins,
        destinations,
        plan_dep,
        act_dep,
        operator_name,
        operator_code,
    )
