from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from api import Credentials, check_response, request, station_endpoint, service_endpoint
from debug import error_msg
from times import get_hourmin_string, get_url, pad_front, to_time, get_status
from network import get_station_crs_from_name, get_station_name_from_crs, station_name_to_code, lnwr_dests


def get_mph_string(speed: float):
    return "{:.2f}".format(speed)


class PlanActDuration:
    def __init__(self, plan: timedelta, act: timedelta = None):
        self.act = act
        self.plan = plan
        if self.act is not None:
            self.diff = int((self.act.total_seconds() -
                             self.plan.total_seconds()) // 60)


class Mileage:
    def __init__(self, miles, chains):
        self.miles = miles
        self.chains = chains
        self.all_miles = miles + (chains / 80)

    def get_string(self):
        return f'{self.miles}m {self.chains}ch'

    def add(self, other):
        miles = self.miles + other.miles
        chains = self.chains + other.chains
        miles = miles + int(chains / 80)
        chains = chains % 80
        return Mileage(miles, chains)

    def subtract(self, other):
        miles = self.miles - other.miles
        chains = self.chains - other.chains
        if (chains < 0):
            miles = miles - 1
            chains = 80 + chains
        return Mileage(miles, chains)

    def speed(self, dur: timedelta):
        hours = (dur.total_seconds() / 3600)
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
        return f'{self.pounds}.{pad_front(self.pence, 2)}'

    def per_mile(self, distance: Mileage):
        return Price(self.all_pounds / distance.all_miles)

    def add(self, other: float):
        return Price(self.all_pounds + other)


class ShortLocation:
    def __init__(self, loc):
        self.name = loc["description"]
        self.crs = get_station_crs_from_name(self.name)
        timestr = loc["publicTime"]
        self.time = time(int(timestr[0:2]), int(timestr[2:4]))


def get_multiple_location_string(locs: list[ShortLocation]):
    for i, loc in enumerate(locs):
        if i == 0:
            string = loc.name
        else:
            string = string + " and " + loc.name
    return string


class ServiceAtStation:
    def __init__(self, service):
        self.origins = map(lambda x: ShortLocation(
            x), service["locationDetail"].get("origin"))
        self.destinations = map(lambda x: ShortLocation(
            x), service["locationDetail"].get("destination"))
        self.platform = service["locationDetail"].get("platform")

        self.plan_dep = service["locationDetail"]["gbttBookedDeparture"]
        self.act_dep = service["locationDetail"].get("realtimeDeparture")

        self.toc = service["atocName"]
        self.service_id = service["serviceUid"]
        self.headcode = service["trainIdentity"]
        run_date = service["runDate"]
        self.date = date(int(run_date[0:4]), int(
            run_date[5:7]), int(run_date[8:10]))

    def get_string(self):
        return f'{self.headcode} {self.origin[0].time} {get_multiple_location_string(self.origins)} to {get_multiple_location_string(self.destinations)}'


class Station:
    def __init__(self, crs: str, dt: datetime, creds: Credentials):
        self.name = get_station_name_from_crs(crs)
        self.crs = crs
        self.datetime = dt
        endpoint = f"{station_endpoint}{self.crs}/{get_url(dt)}"
        response = request(endpoint, creds)
        check_response(response)
        station = response.json()
        self.tiploc = station["location"]["tiploc"]
        self.services = list(map(lambda service: ServiceAtStation(
            service), station["services"]))

    def filter_services_by_time(self, earliest: datetime, latest: datetime):
        filtered_services: list[ServiceAtStation] = []
        for service in self.services:
            dep = datetime.combine(service.date, to_time(service.plan_dep))
            if dep >= earliest and dep <= latest:
                filtered_services.append(service)
        return filtered_services

    def filter_services_by_time_and_stop(self, earliest: datetime, latest: datetime, origin_crs: str, destination_crs: str, creds: Credentials):
        time_filtered: list = self.filter_services_by_time(earliest, latest)
        stop_filtered: list[Service] = []
        for service in time_filtered:
            full_service = Service(service.service_id, service.date, creds)
            if full_service.stops_at_station(origin_crs, destination_crs):
                stop_filtered.append(full_service)
        return stop_filtered


class PlanActTime:
    def __init__(self, date: date, plan: str, act: str):
        if plan is not None:
            self.plan = datetime.combine(date, to_time(plan))
        else:
            self.plan = None

        if act is not None:
            self.act = datetime.combine(date, to_time(act))
            if plan is not None:
                if self.act < self.plan:
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


def duration_from_times(origin_plan: datetime, origin_act: datetime, destination_plan: datetime, destination_act: datetime):
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
        self.arr = PlanActTime(date,
                               loc.get("gbttBookedArrival"), loc.get("realtimeArrival"))
        self.dep = PlanActTime(date,
                               loc.get("gbttBookedDeparture"), loc.get("realtimeDeparture"))
        self.platform = loc.get("platform")
        if self.platform is None:
            self.platform = "-"


@dataclass
class StopTree:
    node: Location
    nexts: list


def get_calls(stop_tree, origin, dest, boarded=False):
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
        if next_chain is not None:
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
    for (i, next) in enumerate(stop_tree.nexts):
        print_stop_tree(next, level+i)


def get_stop_tree(locations, origin, date: datetime, credentials, current_id, parent_id=""):
    boarded = False
    current_nexts = []
    for call in reversed(locations):
        boarded = True
        current_location = Location(date, call)
        assocs = call.get("associations")
        if assocs is not None:
            for assoc in assocs:
                if assoc["type"] == "divide" and not assoc["associatedUid"] == parent_id:
                    assoc_uid = assoc["associatedUid"]
                    assoc_date = datetime.strptime(
                        assoc["associatedRunDate"], "%Y-%m-%d")
                    assoc_date_url = assoc_date.strftime("%Y/%m/%d")
                    endpoint = f"{service_endpoint}{assoc_uid}/{assoc_date_url}"
                    response = request(endpoint, credentials)
                    check_response(response)
                    service_json = response.json()
                    head_node = get_stop_tree(
                        service_json["locations"], origin, assoc_date, credentials, assoc_uid, current_id)
                    current_nexts.append(head_node)
        current_node = StopTree(current_location, current_nexts)
        current_nexts = [current_node]
    return current_node


class Service:
    def __init__(self, service: str, d: datetime, credentials: Credentials):
        endpoint = f"{service_endpoint}{service}/{get_url(d, False)}"
        response = request(endpoint, credentials)
        check_response(response)
        service_json = response.json()
        self.date = d
        self.origins = list(map(ShortLocation, service_json["origin"]))
        self.destinations = list(
            map(ShortLocation, service_json["destination"]))
        self.uid = service_json["serviceUid"]
        self.headcode = service_json["trainIdentity"]
        self.power = service_json["powerType"]
        self.tocCode = service_json["atocCode"]

        lnwr = False

        self.toc = service_json["atocName"]

        if self.toc == "LNER":
            self.toc = "London North Eastern Railway"

        if self.toc == "West Midlands Trains":
            for loc in self.origins:
                if loc.crs in lnwr_dests:
                    lnwr = True
                    break
            for loc in self.destinations:
                if loc.crs in lnwr_dests:
                    lnwr = True
                    break
            if lnwr:
                self.toc = "London Northwestern Railway"
            else:
                self.toc = "West Midlands Railway"

        self.calls = get_stop_tree(
            service_json["locations"], service_json["origin"], d, credentials, self.uid)
        print_stop_tree(self.calls)

    def origin(self):
        return self.calls[0]

    def destination(self):
        return self.calls[-1]

    def stops_at_station(self, origin: str, stn: str):
        return stops_at_station(self.calls, origin, stn)

    def get_arr_at(self, crs: str):
        return get_arr_at(self.calls, crs)

    def get_dep_from(self, crs: str, plan: bool):
        return get_dep_from(self.calls, crs, plan)

    def get_string(self, crs: str):
        string = f"{self.headcode} {get_hourmin_string(self.origins[0].time)} {get_multiple_location_string(self.origins)} to {get_multiple_location_string(self.destinations)}"
        act = get_hourmin_string(self.get_dep_from(crs, False))
        plan = get_hourmin_string(self.get_dep_from(crs, True))
        return f"{string} plan {plan} act {act} ({self.toc})"


class Leg:
    def __init__(self, service: Service, origin_crs: str, dest_crs: str, distance: Mileage, stock: str):
        self.date = service.date
        self.service_origins = service.origins
        self.service_destinations = service.destinations
        self.headcode = service.headcode
        self.toc = service.toc
        self.uid = service.uid

        self.calls = get_calls(service.calls, origin_crs, dest_crs)
        self.leg_origin = self.calls[0]
        self.leg_destination = self.calls[-1]
        self.duration = duration_from_times(
            self.calls[0].dep.plan, self.calls[0].dep.act, self.calls[-1].arr.plan, self.calls[-1].arr.act)
        self.distance = distance
        self.stock = stock
        if self.duration.act is not None:
            self.speed = self.distance.speed(self.duration.act)
        else:
            self.speed = self.distance.speed(self.duration.plan)


class Journey:
    def __init__(self, legs: list[Leg], cost: Price, distance: Mileage, duration: PlanActDuration):
        self.legs = legs
        self.no_legs = len(legs)
        self.cost = cost
        self.cost_per_mile = cost.per_mile(distance)
        self.distance = distance
        self.duration = duration
        if duration.act is not None:
            self.speed = distance.speed(duration.act)
        else:
            self.speed = None
        self.delay = 0
        for leg in legs:
            if leg.leg_destination.arr.diff is not None:
                self.delay = self.delay + leg.leg_destination.arr.diff
