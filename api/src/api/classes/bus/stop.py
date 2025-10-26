from dataclasses import dataclass
from datetime import datetime

from api.db.types.bus import BusStopDetails


@dataclass
class BusStopDeparture:
    service: str
    destination: str
    dep_time: datetime
    bustimes_journey_id: int


def short_string_of_bus_stop_departure(departure: BusStopDeparture) -> str:
    return f"{departure.dep_time.strftime('%H:%M')}: {departure.service} to {departure.destination}"


def short_string_of_bus_stop_details(bus_stop: BusStopDetails) -> str:
    if bus_stop.indicator is None:
        indicator_text = ""
    else:
        indicator_text = f" ({bus_stop.indicator})"
    return f"{bus_stop.stop_name}{indicator_text}, {bus_stop.locality_name} ({bus_stop.atco_code})"
