import json
from datetime import time, date, datetime, timedelta
from api import Credentials

from structs.network import get_matching_station_names, get_station_crs_from_name, get_station_name_from_crs
from scraper import get_mileage_for_service_call
from structs.time import get_diff_struct, get_duration_string, pad_front, add, get_hourmin_string, get_diff_string, get_duration, to_time, get_status
from structures import Journey, Leg, Mileage, PlanActDuration, PlanActTime, Price, Service, ShortLocation, Station, Location, add_durations, get_mph_string, new_duration
from debug import debug_msg


def get_input_price(prompt):
    while True:
        string = input(f"{prompt} ")
        try:
            parts = string.replace("£", "").split(".")
            if len(parts) == 2 or len(parts) == 1:
                if len(parts) == 1:
                    pence = 0
                else:
                    pence = int(parts[1])
                pounds = int(parts[0])
                if pounds >= 0 and pence >= 0 and pence < 100:
                    return Price(pounds, pence)
        except:
            print(f"Expected price but got '{string}'")


def get_station_string(prompt: str, stn: Station | None = None):
    """
    Get a string specifying a station from a user.
    Can either be a three letter code (in which case confirmation will be asked for)
    or a full station name
    """
    if stn is not None:
        prompt = f"{prompt} ({get_station_name_from_crs(stn.crs)})"
    prompt = f'{prompt}: '
    while True:
        string = input(prompt).upper()
        # We only search for strings of length at least three, otherwise there would be loads
        if len(string) == 0 and stn is not None:
            return stn.crs
        if len(string) >= 3:
            # Check the three letter codes first
            if string in station_codes:
                name = station_code_to_name[string]
                # Just check that it's right, often the tlc is a guess
                resp = yes_or_no(f"Did you mean {name}?")
                if resp:
                    return get_station_crs_from_name(name)
            # Otherwise search for substrings in the full names of stations
            matches = get_matching_station_names(string.lower().strip())
            if len(matches) == 0:
                print("No matches found, try again")
            elif len(matches) == 1:
                match = matches[0]
                resp = yes_or_no(f"Did you mean {match}?")
                if resp:
                    return get_station_crs_from_name(match)
            else:
                print("Multiple matches found: ")
                choice = pick_from_list(matches, "Select a station", True)
                if choice is not None:
                    return get_station_crs_from_name(choice)
        else:
            print("Search string must be at least three characters")


def get_service(station: Station, destination_crs: str, creds: Credentials):
    """
    Record a new journey in the logfile
    """

    while True:
        services = station.services
        if services is not None:
            # We want to search within a smaller timeframe
            timeframe = 15

            earliest_time = add(station.datetime, -timeframe)
            latest_time = add(station.datetime, timeframe)
            # The results encompass a ~1 hour period
            # We only want to check our given timeframe
            # We also only want services that stop at our destination
            filtered_services = station.filter_services_by_time_and_stop(
                earliest_time, latest_time, station.crs, destination_crs, creds
            )

            debug_msg("Searching for services from " + station.name)
            choice = pick_from_list(
                filtered_services, "Pick a service", True, lambda x: x.get_string(station.crs))

            if choice is not None:
                return choice
        else:
            print("No services found!")


def get_stock(service: Service):
    # Currently getting this automatically isn't implemented
    # We could trawl wikipedia and make a map of which trains operate which services
    # Or if know your train becomes part of the api
    stock = pick_from_list(stock_dict[service.toc], "Stock", False)
    return stock


def compute_mileage(service: Service, origin: str, destination: str) -> Mileage:
    origin_mileage = get_mileage_for_service_call(service, origin)
    destination_mileage = get_mileage_for_service_call(
        service, destination)
    return destination_mileage.subtract(origin_mileage)


def get_mileage():
    # If we can get a good distance set this could be automated
    miles = get_input_no("Miles")
    chains = get_input_no("Chains", 79)
    return Mileage(miles, chains)


def make_short_loc_entry(loc: ShortLocation, origin: bool):
    entry = {
        "name": loc.name,
        "crs": loc.crs
    }
    time_string = get_hourmin_string(loc.time)
    if origin:
        entry["dep_plan"] = time_string
    else:
        entry["arr_plan"] = time_string
    return entry


def make_planact_entry(planact: PlanActTime):
    entry = {}
    if planact.plan is not None:
        entry["plan"] = get_hourmin_string(planact.plan)
    if planact.act is not None:
        entry["act"] = get_hourmin_string(planact.act)
    if planact.diff is not None:
        entry["diff"] = get_diff_string(planact.diff)
        entry["status"] = planact.status
    return entry


def make_loc_entry(loc: Location, arr: bool = True, dep: bool = True):
    entry = {
        "name": loc.name,
        "crs": loc.crs,
        "platform": loc.platform
    }
    if arr:
        entry["arr"] = make_planact_entry(loc.arr)
    if dep:
        entry["dep"] = make_planact_entry(loc.dep)
    return entry


def make_leg_entry(leg: Leg):

    entry = {
        "date": {
            "year": leg.date.year,
            "month": pad_front(leg.date.month, 2),
            "day": pad_front(leg.date.day, 2),
        },
        "operator": leg.toc,
        "mileage": {
            "miles": leg.distance.miles,
            "chains": leg.distance.chains
        },
        "uid": leg.uid,
        "headcode": leg.headcode,
        "stock": leg.stock,
        "delay": get_diff_string(leg.duration.diff),
        "status": get_status(leg.duration.diff),
        "service_origins": list(map(lambda x: make_short_loc_entry(x, True), leg.service_origins)),
        "service_destinations": list(map(lambda x: make_short_loc_entry(x, False), leg.service_destinations)),
        "leg_origin": make_loc_entry(leg.leg_origin, False, True),
        "leg_destination": make_loc_entry(leg.leg_destination, True, False),
        "stops": list(map(lambda x: make_loc_entry(x), leg.calls)),
    }

    duration = {
        "plan": get_duration_string(leg.duration.plan)
    }
    if leg.duration.act is not None:
        duration["act"] = get_duration_string(leg.duration.act)
        duration["diff"] = leg.duration.diff
        entry["speed"] = get_mph_string(leg.distance.speed(leg.duration.act))
    entry["duration"] = duration

    return entry


def make_journey_entry(journey: Journey):
    entry = {
        "legs": list(map(make_leg_entry, journey.legs)),
        "no_legs": journey.no_legs,
        "cost": journey.cost.to_string(),
        "cost_per_mile": journey.cost_per_mile.to_string(),
        "distance": {
            "miles": journey.distance.miles,
            "chains": journey.distance.chains,
        },
        "duration": {
            "plan": get_duration_string(journey.duration.plan)
        },
        "delay": get_diff_string(journey.delay),
        "status": get_status(journey.delay)
    }

    if journey.duration.act is not None:
        entry["duration"]["act"] = get_duration_string(journey.duration.act)
        entry["duration"]["diff"] = get_diff_string(journey.duration.diff)

    if journey.speed is not None:
        entry["speed"] = journey.speed
    return entry


def record_new_leg(start: datetime | None, station: Station | None, creds: Credentials):
    origin_crs = get_station_string("Origin", station)
    destination_crs = get_station_string("Destination")
    dt = get_datetime(start)
    origin_station = Station(origin_crs, dt, creds)
    service = get_service(origin_station, destination_crs, creds)
    stock = get_stock(service)
    mileage = compute_mileage(service, origin_crs, destination_crs)
    leg = Leg(service, origin_crs, destination_crs, mileage, stock)
    return leg


def record_new_journey(creds: Credentials):
    legs = []
    dt = None
    distance = Mileage(0, 0)
    duration = new_duration()
    delay = 0
    station = None
    while True:
        leg = record_new_leg(dt, station, creds)
        legs.append(leg)
        # update the running totals for distance and duration
        distance = distance.add(leg.distance)
        duration = add_durations(duration, leg.duration)
        # get the end of this leg since it potentially might be the start of the next
        station = leg.leg_destination
        if leg.leg_destination.arr.act is not None:
            dt = leg.leg_destination.arr.act
        else:
            dt = leg.leg_destination.arr.plan
        # do we want to go around again?
        choice = yes_or_no("Add another leg?")
        if not choice:
            break
    cost = get_input_price("Journey cost?")
    journey = Journey(legs, cost, distance, duration)
    return journey


def add_to_logfile(log_file: str, creds: Credentials):
    journey = record_new_journey(creds)
    log = read_logfile(log_file)
    if log != {}:
        all_journeys = log["journeys"]
        no_journeys = log["no_journeys"]
        no_legs = log["no_legs"]
        delay = int(log["delay"]["diff"])
        duration_act = timedelta_from_string(log["duration"]["act"])
        duration_plan = timedelta_from_string(log["duration"]["plan"])
        duration_diff = int(log["duration"]["diff"])
        miles = log["distance"]["miles"]
        chains = log["distance"]["chains"]
        cost = float(log["cost"])
    else:
        all_journeys = []
        no_journeys = 0
        no_legs = 0
        delay = 0
        duration_act = timedelta()
        duration_plan = timedelta()
        duration_diff = 0
        miles = 0
        chains = 0
        cost = 0.0

    all_journeys.append(make_journey_entry(journey))
    log["journeys"] = all_journeys
    log["no_journeys"] = no_journeys + 1
    log["no_legs"] = no_legs + journey.no_legs
    log["delay"] = get_diff_struct(delay + journey.delay)
    new_duration_act = duration_act + journey.duration.act
    new_duration_plan = duration_plan + journey.duration.plan
    new_duration_diff = duration_diff + journey.duration.diff
    new_distance = Mileage(miles, chains).add(journey.distance)
    log["duration"] = {
        "act": get_duration_string(new_duration_act),
        "plan": get_duration_string(new_duration_plan),
        "diff":  get_diff_string(new_duration_diff)
    }
    log["distance"] = {
        "miles": new_distance.miles,
        "chains": new_distance.chains,
        "total": new_distance.all_miles
    }
    log["speed"] = get_mph_string(new_distance.speed(new_duration_act))
    new_cost = journey.cost.add(cost)
    log["cost"] = new_cost.to_string()
    log["cost_per_mile"] = new_cost.per_mile(new_distance).to_string()
    write_logfile(log, log_file)


def read_logfile(log_file: str):
    log = {}
    try:
        with open(log_file, "r") as input:
            log = json.load(input)
        if log is None:
            log = {}
    except:
        debug_msg(f'Logfile {log_file} not found, making empty log')
    return log


def write_logfile(log: list, log_file: str):
    with open(log_file, "w+") as output:
        json.dump(log, output)
