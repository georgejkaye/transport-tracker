from datetime import date, datetime, time

from api import check_response, filter_services_by_stop, request, station_endpoint, service_endpoint
from time import get_url
from network import station_name_to_code


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

    def speed(self, time: time):
        miles = self.miles + (self.chains / 80)
        hours = time.hour + (time.minute / 60)
        return miles / hours


class ShortLocation:
    def __init__(self, loc):
        self.description = loc["description"]
        self.crs = station_name_to_code(self.description)
        timestr = loc["publicTime"]
        self.time = time(timestr[0:2], timestr[2:4])


def get_multiple_location_string(locs: list[ShortLocation]):
    for i, loc in enumerate(locs):
        if i == 0:
            string = loc["description"]
        else:
            string = string + " and " + loc["description"]
    return string


class ServiceAtStation:
    def __init__(self, service):
        self.origins = map(lambda x: ShortLocation(
            x), service["locationDetail"]["origin"])
        self.destinations = map(lambda x: ShortLocation(
            x), service["locationDetail"]["destination"])
        self.platform = service["locationDetail"]["platform"]
        self.dep = service["locationDetail"]["realtimeDeparture"]
        self.toc = service["atocName"]
        self.service_id = service["serviceUid"]
        self.headcode = service["trainIdentity"]
        run_date = service["runDate"]
        self.date = datetime(run_date[0:4], run_date[5:7], run_date[8:10])

    def get_string(self):
        return f'{self.headcode} {self.origin[0].time} {get_multiple_location_string(self.origins)} to {get_multiple_location_string(self.destinations)}'


class Station:
    def __init__(self, stn: str, dt: datetime):
        endpoint = station_endpoint + stn + "/" + get_url(dt)
        response = request(endpoint)
        check_response(response)
        station = response.json()
        self.datetime = dt
        self.name = station["name"]
        self.crs = station["crs"]
        self.tiploc = station["tiploc"]
        self.services = list(map(lambda service: ServiceAtStation(
            service), station["services"]))

    def filter_services_by_time(self, earliest: datetime, latest: datetime):
        filtered_services: list[ServiceAtStation] = []
        for service in self.services:
            dep = service.dep
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
        return "very-late"
    if diff < 0:
        return "late"
    if diff == 0:
        return "on-time"
    if diff < 5:
        return "early"
    return "very-early"


class PlanActTime:
    def __init__(self, plan: str, act: str):
        self.plan = time(plan[0:2], plan[2:4])
        if act != None:
            self.act = time(act[0:2], act[2:4])
            self.diff = int((self.act - self.plan).total_seconds() / 60)
            self.status = get_status(self.diff)
        else:
            self.act = None
            self.diff = None
            self.status = None


class Location:
    def __init__(self, loc):
        self.name = loc["description"]
        self.crs = loc["crs"]
        self.tiploc = loc["tiploc"]
        self.arr = PlanActTime(
            loc["gbttBookedArrival"], loc.get("realtimeArrival"))
        self.dep = PlanActTime(
            loc["gbttBookedDeparture"], loc.get("realtimeDeparture"))
        self.platform = loc.get("platform")


class Service:
    def __init__(self, service: str, d: date):
        endpoint = service_endpoint + service + get_url(d, False)
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
        self.toc = service["atocName"]
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
