from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional

from train_tracker.api import (
    Credentials,
    check_response,
    request,
    station_endpoint,
    service_endpoint,
)
from train_tracker.data.stations import TrainStation
from train_tracker.debug import error_msg
from train_tracker.times import (
    get_hourmin_string,
    get_url,
    pad_front,
    to_time,
    get_status,
)
from train_tracker.network import (
    get_station_crs_from_name,
    get_station_name_from_crs,
    lnwr_dests,
)


def get_mph_string(speed: float):
    return "{:.2f}".format(speed)


class PlanActDuration:
    def __init__(self, plan: timedelta, act: Optional[timedelta] = None):
        self.act = act
        self.plan = plan
        if self.act is not None:
            self.diff = int(
                (self.act.total_seconds() - self.plan.total_seconds()) // 60
            )


class Mileage:
    def __init__(self, miles, chains):
        self.miles = miles
        self.chains = chains
        self.all_miles = miles + (chains / 80)

    def get_string(self):
        return f"{self.miles}m {self.chains}ch"

    def add(self, other):
        miles = self.miles + other.miles
        chains = self.chains + other.chains
        miles = miles + int(chains / 80)
        chains = chains % 80
        return Mileage(miles, chains)

    def subtract(self, other):
        miles = self.miles - other.miles
        chains = self.chains - other.chains
        if chains < 0:
            miles = miles - 1
            chains = 80 + chains
        return Mileage(miles, chains)

    def speed(self, dur: timedelta):
        hours = dur.total_seconds() / 3600
        return round(self.all_miles / hours, 2)


class Price:
    def __init__(self, *args):
        if len(args) == 1:
            self.all_pounds = round(args[0], 2)
            self.pounds = int(self.all_pounds)
            self.pence = int((self.all_pounds * 100) % 100)
        elif len(args) == 2:
            self.pounds = args[0]
            self.pence = args[1]
            self.all_pounds = self.pounds + (self.pence / 100)
        else:
            error_msg("Bad arguments to Price constructor")
            exit(1)

    def to_string(self):
        return f"{self.pounds}.{pad_front(self.pence, 2)}"

    def per_mile(self, distance: Mileage):
        return Price(self.all_pounds / distance.all_miles)

    def add(self, other: float):
        return Price(self.all_pounds + other)


@dataclass
class ShortLocation:
    station: TrainStation
    dt: datetime


def get_multiple_location_string(locs: list[ShortLocation]):
    string = ""
    for i, loc in enumerate(locs):
        if i == 0:
            string = loc.station.name
        else:
            string = f"{string} and {loc.station.name}"
    return string


class PlanActTime:
    def __init__(self, date: date, plan: str, act: str):
        if plan is not None:
            self.plan = datetime.combine(date, to_time(plan))
        else:
            self.plan = None

        if act is not None:
            self.act = datetime.combine(date, to_time(act))
            if self.plan is not None:
                if self.act < (self.plan - timedelta(hours=12)):
                    self.act = self.act + timedelta(days=1)
        else:
            self.act = None
        if self.plan is not None and self.act is not None:
            self.diff = int((self.act - self.plan).total_seconds() // 60)
            self.status = get_status(self.diff)
        else:
            self.diff = None
            self.status = None


def new_duration():
    return PlanActDuration(timedelta(), timedelta())


def duration_from_times(
    origin_plan: datetime | None,
    origin_act: datetime | None,
    destination_plan: datetime | None,
    destination_act: datetime | None,
):
    if origin_plan is None or destination_plan is None:
        plan = timedelta(0)
    else:
        plan = destination_plan - origin_plan
    if origin_act is not None and destination_act is not None:
        act = destination_act - origin_act
    else:
        act = None
    return PlanActDuration(plan, act)


def add_durations(a: PlanActDuration, b: PlanActDuration):
    plan = a.plan + b.plan
    if a.act is not None and b.act is not None:
        act = a.act + b.act
    else:
        act = None
    return PlanActDuration(plan, act)


class Location:
    def __init__(self, date: date, loc):
        self.name = loc["description"]
        self.crs = loc["crs"]
        self.tiploc = loc["tiploc"]
        self.arr = PlanActTime(
            date, loc.get("gbttBookedArrival"), loc.get("realtimeArrival")
        )
        self.dep = PlanActTime(
            date, loc.get("gbttBookedDeparture"), loc.get("realtimeDeparture")
        )
        self.platform = loc.get("platform")
        if self.platform is None:
            self.platform = "-"


@dataclass
class StopTree:
    node: Location
    nexts: list


def get_calls(stop_tree, origin, dest, boarded=False) -> Optional[list[Location]]:
    node = stop_tree.node
    if boarded:
        if node.crs == dest:
            return [node]
        else:
            new_boarded = True
    elif node.crs == origin:
        new_boarded = True
    else:
        new_boarded = False
    for next in stop_tree.nexts:
        next_chain = get_calls(next, origin, dest, new_boarded)
        if new_boarded and next_chain is not None:
            next_chain.insert(0, node)
        return next_chain
    return None


def stops_at_station(stop_tree, origin, stn, reached=False):
    if not reached:
        if stop_tree.node.crs == origin:
            new_reached = True
        else:
            new_reached = False
    elif stop_tree.node.crs == stn:
        return True
    else:
        new_reached = True
    for next in stop_tree.nexts:
        if stops_at_station(next, origin, stn, new_reached):
            return True
    return False


def get_dep_from(stop_tree, crs, plan):
    if stop_tree.node.crs == crs:
        dep = stop_tree.node.dep
        if dep.act is not None and not plan:
            return dep.act
        return dep.plan
    else:
        for next in stop_tree.nexts:
            dep = get_dep_from(next, crs, plan)
            if dep is not None:
                return dep
        return None


def get_arr_at(stop_tree, crs):
    if stop_tree.node.crs == crs:
        arr = stop_tree.node.arr
        if arr.act is not None:
            return arr.act
        return arr.plan


def print_stop_tree(stop_tree, level=0):
    print(f"{'-' * level} | {stop_tree.node.name} ({stop_tree.node.crs})")
    for i, next in enumerate(stop_tree.nexts):
        print_stop_tree(next, level + i)


def get_stop_tree(
    locations, origin, date: datetime, credentials, current_id, parent_id=""
):
    current_nexts = []
    for call in reversed(locations):
        if call.get("crs") is not None:
            current_location = Location(date, call)
            assocs = call.get("associations")
            if assocs is not None:
                for assoc in assocs:
                    if (
                        assoc["type"] == "divide"
                        and not assoc["associatedUid"] == parent_id
                    ):
                        assoc_uid = assoc["associatedUid"]
                        assoc_date = datetime.strptime(
                            assoc["associatedRunDate"], "%Y-%m-%d"
                        )
                        assoc_date_url = assoc_date.strftime("%Y/%m/%d")
                        endpoint = f"{service_endpoint}{assoc_uid}/{assoc_date_url}"
                        response = request(endpoint, credentials)
                        check_response(response)
                        service_json = response.json()
                        if service_json.get("locations") is not None:
                            head_node = get_stop_tree(
                                service_json["locations"],
                                origin,
                                assoc_date,
                                credentials,
                                assoc_uid,
                                current_id,
                            )
                            current_nexts.append(head_node)
            current_node = StopTree(current_location, current_nexts)
            current_nexts = [current_node]
    return current_node
