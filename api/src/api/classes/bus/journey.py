from dataclasses import dataclass

from api.db.types.bus import (
    BusCallInData,
    BusOperatorDetails,
    BusServiceDetails,
)


def string_of_bus_call_in(bus_call: BusCallInData) -> str:
    if bus_call.plan_arr is not None:
        time_string = f" arr {bus_call.plan_arr.strftime('%H:%M')}"
    else:
        time_string = ""
    if bus_call.plan_dep is not None:
        time_string = f"{time_string} dep {bus_call.plan_dep.strftime('%H:%M')}"
    return f"{bus_call.stop_name}{time_string}"


@dataclass
class BusJourneyTimetable:
    id: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    calls: list[BusCallInData]
