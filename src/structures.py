from datetime import date, datetime, time, timedelta

from api import check_response, request, station_endpoint, service_endpoint
from times import get_hourmin_string, get_url, to_time
from network import get_station_crs_from_name, get_station_name_from_crs, station_name_to_code, lnwr_dests


def get_mph_string(speed: float):
    return "{:.2f}".format(speed)


class Mileage:
    def __init__(self, miles, chains):
        self.miles = miles
        self.chains = chains

    def get_string(self):
        return f'{self.miles}m {self.chains}ch'

    def add(self, other):
        miles = self.miles + other.miles
        chains = self.chains + other.chains
        miles = miles + int(chains / 80)
        chains = chains % 80
        return Mileage(miles, chains)

    def speed(self, time: timedelta):
        miles = self.miles + (self.chains / 80)
        hours = (time.seconds / 3600)
        return round(miles / hours, 2)


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
            x), service["locationDetail"]["origin"])
        self.destinations = map(lambda x: ShortLocation(
            x), service["locationDetail"]["destination"])
        self.platform = service["locationDetail"]["platform"]

        self.dep = service["locationDetail"].get("realtimeDeparture")
        if self.dep is None:
            self.dep = service["locationDetail"].get("gbttPlannedDeparture")

        self.toc = service["atocName"]
        self.service_id = service["serviceUid"]
        self.headcode = service["trainIdentity"]
        run_date = service["runDate"]
        self.date = date(int(run_date[0:4]), int(
            run_date[5:7]), int(run_date[8:10]))

    def get_string(self):
        return f'{self.headcode} {self.origin[0].time} {get_multiple_location_string(self.origins)} to {get_multiple_location_string(self.destinations)}'


class Station:
    def __init__(self, crs: str, dt: datetime):
        self.name = get_station_name_from_crs(crs)
        self.crs = crs
        self.datetime = dt
        endpoint = f"{station_endpoint}{self.crs}/{get_url(dt)}"
        response = request(endpoint)
        check_response(response)
        station = response.json()
        self.tiploc = station["location"]["tiploc"]
        self.services = list(map(lambda service: ServiceAtStation(
            service), station["services"]))

    def filter_services_by_time(self, earliest: datetime, latest: datetime):
        filtered_services: list[ServiceAtStation] = []
        for service in self.services:
            if service.dep is not None:
                dep = datetime.combine(service.date, to_time(service.dep))
                if dep >= earliest and dep <= latest:
                    filtered_services.append(service)
        return filtered_services

    def filter_services_by_time_and_stop(self, earliest: datetime, latest: datetime, origin_crs: str, destination_crs: str):
        time_filtered: list = self.filter_services_by_time(earliest, latest)
        stop_filtered: list[Service] = []
        for service in time_filtered:
            full_service = Service(service.service_id, service.date)
            if full_service.stops_at_station(origin_crs, destination_crs):
                stop_filtered.append(full_service)
        return stop_filtered


def get_status(diff: int):
    if diff <= -5:
        return "very-early"
    if diff < 0:
        return "early"
    if diff == 0:
        return "on-time"
    if diff < 5:
        return "late"
    return "very-late"


class PlanActTime:
    def __init__(self, plan: str, act: str):
        if plan is not None:
            self.plan = to_time(plan)
        else:
            self.plan = None
        if act is not None:
            self.act = to_time(act)
        else:
            self.act = None

        if self.plan is not None and self.act is not None:
            self.diff = int((datetime.combine(date.today(), self.act) -
                            datetime.combine(date.today(), self.plan)).total_seconds() / 60)
            self.status = get_status(self.diff)
        else:
            self.diff = None
            self.status = None


class Location:
    def __init__(self, loc):
        self.name = loc["description"]
        self.crs = loc["crs"]
        self.tiploc = loc["tiploc"]

        self.arr = PlanActTime(
            loc.get("gbttBookedArrival"), loc.get("realtimeArrival"))
        self.dep = PlanActTime(
            loc.get("gbttBookedDeparture"), loc.get("realtimeDeparture"))
        self.platform = loc.get("platform")


class Service:
    def __init__(self, service: str, d: date):
        endpoint = f"{service_endpoint}{service}/{get_url(d, False)}"
        response = request(endpoint)
        check_response(response)
        service = response.json()
        self.date = d
        self.origins = list(map(ShortLocation, service["origin"]))
        self.destinations = list(map(ShortLocation, service["destination"]))
        self.uid = service["serviceUid"]
        self.headcode = service["trainIdentity"]
        self.power = service["powerType"]
        self.tocCode = service["atocCode"]

        lnwr = False

        self.toc = service["atocName"]

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

        self.calls = list(map(lambda x: Location(x), service["locations"]))

    def origin(self):
        return self.calls[0]

    def destination(self):
        return self.calls[-1]

    def stops_at_station(self, origin: str, stn: str):
        reached = False
        for loc in self.calls:
            if not reached:
                if loc.crs == origin:
                    reached = True
            elif loc.crs == stn:
                return True
        return False

    def get_arr_at(self, crs: str):
        for loc in self.calls:
            if loc.crs == crs:
                arr = loc.arr
                if arr.act is not None:
                    return datetime.combine(self.date, arr.act)
                return datetime.combine(self.date, arr.plan)

    def get_dep_from(self, crs: str, plan: bool):
        for loc in self.calls:
            if loc.crs == crs:
                dep = loc.dep
                if dep.act is not None and not plan:
                    return datetime.combine(self.date, dep.act)
                return datetime.combine(self.date, dep.plan)

    def get_string(self, crs: str):
        string = f"{self.headcode} {get_hourmin_string(self.origins[0].time)} {get_multiple_location_string(self.origins)} to {get_multiple_location_string(self.destinations)}"
        act = get_hourmin_string(self.get_dep_from(crs, False))
        plan = get_hourmin_string(self.get_dep_from(crs, True))
        return f"{string} plan {plan} act {act} ({self.toc})"