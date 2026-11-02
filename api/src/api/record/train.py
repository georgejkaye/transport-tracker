from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional, Sequence, Tuple

from api.train.service.graph.builder import (
    build_service_graph,
    get_service_graph_segments,
    get_services_dict_from_service,
)
from api.train.service.graph.classes import (
    ServiceGraphChildRelation,
    ServiceGraphNode,
    ServiceGraphParentRelation,
)
from psycopg import Connection

from api.classes.interactive import PickMultiple, PickSingle, PickUnknown
from api.classes.train.stock import (
    StockReport,
    StockSegment,
    sort_by_classes,
    sort_by_subclasses,
    string_of_class,
    string_of_class_and_subclass,
    string_of_stock_report,
)
from api.db.functions.insert.train.leg import insert_train_leg_fetchone
from api.db.functions.select.train.operator import (
    select_train_operator_by_operator_code_fetchone,
)
from api.db.functions.select.train.station import (
    select_train_station_by_crs_fetchone,
    select_train_stations_by_name_substring_fetchall,
)
from api.db.functions.select.train.stock import (
    select_train_operator_stock_fetchall,
)
from api.db.types.register import register_types
from api.db.types.train.leg import (
    TrainLegAssociatedServiceInData,
    TrainLegCallCallInData,
    TrainLegCallInData,
    TrainLegInData,
    TrainLegServiceCallInData,
    TrainLegServiceEndpointInData,
    TrainLegServiceInData,
    TrainLegStockSegmentInData,
)
from api.db.types.train.operator import TrainBrandOutData, TrainOperatorOutData
from api.db.types.train.station import TrainStationOutData
from api.db.types.train.stock import (
    TrainStockOutData,
    TrainStockSubclassOutData,
)
from api.pull.train.api import RttApiManager
from api.pull.train.classes.gbnr.location import RttGbnrLocationService
from api.pull.train.classes.gbnr.service import (
    RttGbnrServiceData,
    RttGbnrServiceLocation,
)
from api.pull.train.classes.location import (
    RttLocationPair,
)
from api.pull.train.classes.service import (
    get_rtt_association_type_db_int,
)
from api.pull.train.classes.stock import StockChange
from api.pull.train.clients.api import RttApiClient
from api.pull.train.clients.gbnr import RttGbnrClient
from api.record.user import get_users_from_input
from api.utils.database import connect_with_env
from api.utils.interactive import (
    get_choice_from_input,
    get_choice_from_input_paginate,
    get_choices_from_input,
    get_confirmation_from_input,
    get_datetime_from_input,
    get_int_from_input,
    get_text_from_input,
    print_error,
    print_information,
)
from api.utils.mileage import (
    miles_and_chains_to_miles,
    string_of_miles_and_chains,
)
from api.utils.times import (
    add,
    get_hourmin_string,
)


class TrainRecorder:
    def __init__(
        self,
        db_conn: Connection,
        rtt_rtt_client: RttGbnrClient,
    ):
        self.db_conn = db_conn
        self.rtt_gbnr_client = rtt_rtt_client

    def record_train_leg(self) -> None:
        users = get_users_from_input(self.db_conn)
        if len(users) == 0:
            return None
        leg = self._get_train_leg_from_input()
        if leg is None:
            print_error("Could not get train leg")
            return
        result = insert_train_leg_fetchone(
            self.db_conn, [user.user_id for user in users], leg
        )
        if result is None:
            print_error("Could not insert train leg")
            return
        print_information(f"Recorded train leg {result.train_leg_id}")

    def _get_station_from_input(
        self, prompt: str, default_station: TrainStationOutData | None = None
    ) -> Optional[TrainStationOutData]:
        if default_station is not None:
            full_prompt = f"{prompt} ({default_station.station_name})"
            default_string = default_station.station_crs
        else:
            full_prompt = prompt
            default_string = ""
        while True:
            input_string_opt = get_text_from_input(
                full_prompt, default=default_string, min_length=3
            )
            if input_string_opt is None:
                return None
            input_string = input_string_opt.lower()
            if len(input_string) == 0 and default_station is not None:
                return default_station
            if len(input_string) == 3:
                crs_station = select_train_station_by_crs_fetchone(
                    self.db_conn, input_string
                )
                if crs_station is not None:
                    resp = get_confirmation_from_input(
                        f"Did you mean {crs_station.station_name}"
                    )
                    if resp:
                        return crs_station
            matches = select_train_stations_by_name_substring_fetchall(
                self.db_conn, input_string
            )
            if len(matches) == 0:
                print_information("No matches found, try again")
            elif len(matches) == 1:
                match = matches[0]
                resp = get_confirmation_from_input(
                    f"Did you mean {match.station_name}?"
                )
                if resp:
                    return match
            else:
                print_information("Multiple matches found: ")
                choice = get_choice_from_input_paginate(
                    "Select a station",
                    matches,
                    display=lambda x: x.station_name,
                )
                match choice:
                    case PickSingle(default_station):
                        return default_station
                    case _:
                        return None

    def _get_service_at_station_string(
        self, service: RttGbnrLocationService
    ) -> str:
        origin_string = self._get_multiple_short_station_string(service.origin)
        destination_string = self._get_multiple_short_station_string(
            service.destination
        )
        plan_string = get_hourmin_string(service.get_plan_dep())
        act_string = get_hourmin_string(service.get_act_dep())
        operator = service.get_operator()
        operator_string = operator.name
        return f"{origin_string} to {destination_string} plan {plan_string} act {act_string} ({operator_string})"

    def _get_service_at_station_from_input(
        self,
        origin: TrainStationOutData,
        search_datetime: datetime,
        destination: TrainStationOutData,
    ) -> Optional[RttGbnrLocationService]:
        timeframe = 15
        earliest_time = add(search_datetime, -timeframe)
        latest_time = add(search_datetime, timeframe)
        services = self.rtt_gbnr_client.get_location(
            origin.station_crs,
            time_from=earliest_time.isoformat(),
            time_to=latest_time.isoformat(),
            filter_to=destination.station_crs,
        ).services
        if len(services) == 0:
            return None
        choice = get_choice_from_input_paginate(
            "Pick a service",
            services,
            display=self._get_service_at_station_string,
        )
        match choice:
            case PickSingle(service):
                return service
            case _:
                return None

    def _get_unit_class_from_input(
        self,
        operator_stock: list[TrainStockOutData],
    ) -> Optional[PickUnknown | PickSingle[TrainStockOutData]]:
        chosen_class = get_choice_from_input(
            "Class number",
            sort_by_classes(operator_stock),
            unknown=True,
            display=string_of_class,
        )
        match chosen_class:
            case None:
                return None
            case PickUnknown():
                return chosen_class
            case PickSingle(_):
                return chosen_class
            case _:
                return None

    def _get_unit_subclass_from_input(
        self,
        stock: TrainStockOutData,
    ) -> Optional[PickUnknown | PickSingle[TrainStockSubclassOutData]]:
        if len(stock.stock_subclasses) == 1:
            return PickSingle(stock.stock_subclasses[0])
        else:
            chosen_subclass = get_choice_from_input(
                "Subclass no",
                sort_by_subclasses(stock.stock_subclasses),
                unknown=True,
                cancel=False,
                display=lambda c: string_of_class_and_subclass(stock, c),
            )
            match chosen_subclass:
                case None:
                    return None
                case PickUnknown():
                    return chosen_subclass
                case PickSingle(_):
                    return chosen_subclass
                case _:
                    return None

    def _get_unit_no_from_input(
        self,
        stock_class: TrainStockOutData,
    ) -> Optional[int]:
        while True:
            unit_no_opt = get_int_from_input(
                "Stock number",
                lower=stock_class.stock_class * 1000,
                upper=stock_class.stock_class * 1000 + 999,
                unknown=True,
            )
            return unit_no_opt

    def _get_unit_cars_from_input(
        self,
        stock_class: TrainStockOutData,
        stock_subclass: TrainStockSubclassOutData,
    ) -> PickUnknown | PickSingle[int] | None:
        if len(stock_subclass.stock_cars) == 1:
            print_information(
                f"{string_of_class_and_subclass(stock_class, stock_subclass, name=False)} always has {stock_subclass.stock_cars[0]} cars"
            )
            return PickSingle(stock_subclass.stock_cars[0])
        result = get_choice_from_input(
            "Number of cars",
            stock_subclass.stock_cars,
            lambda c: f"{c} car{'s' if c > 1 else ''}",
            unknown=True,
        )
        match result:
            case None:
                return None
            case PickUnknown():
                return result
            case PickSingle(_):
                return result
            case _:
                return None

    def _get_call_from_input(
        self,
        current: TrainLegCallInData,
        calls: list[TrainLegCallInData],
    ) -> Optional[Tuple[TrainLegCallInData, int, list[TrainLegCallInData]]]:
        end_call = get_choice_from_input_paginate(
            f"Stock formation from {current.station_name} until",
            [(i, call) for (i, call) in enumerate(calls)],
            display=lambda x: f"{x[1].station_name} ({x[1].station_crs})",
        )
        match end_call:
            case PickSingle((i, call)):
                return (call, i, calls[i + 1 :])
            case PickUnknown():
                return None
            case _:
                raise RuntimeError()

    def _get_unit_report_from_input(
        self,
        stock_list: list[TrainStockOutData],
    ) -> Optional[StockReport]:
        stock_class_input = self._get_unit_class_from_input(stock_list)
        stock_data = self._get_stock_data(stock_class_input)
        stock_subclass_data = self._get_stock_subclass_data(stock_data)
        stock_unit_no = self._get_stock_no(stock_data, stock_subclass_data)
        stock_cars = self._get_stock_cars(stock_data, stock_subclass_data)
        return StockReport(
            stock_data.stock_class if stock_data is not None else None,
            (
                stock_subclass_data.stock_subclass
                if stock_subclass_data is not None
                else None
            ),
            stock_unit_no,
            stock_cars,
        )

    def _get_stock_data(
        self,
        stock_class_input: Optional[
            PickUnknown | PickSingle[TrainStockOutData]
        ],
    ) -> Optional[TrainStockOutData]:
        match stock_class_input:
            case PickSingle(stock_class_choice):
                return stock_class_choice
            case _:
                return None

    def _get_stock_subclass_data(
        self, stock_data: Optional[TrainStockOutData]
    ) -> Optional[TrainStockSubclassOutData]:
        if stock_data is not None:
            stock_subclass_input = self._get_unit_subclass_from_input(
                stock_data
            )
            match stock_subclass_input:
                case PickSingle(stock_subclass_choice):
                    return stock_subclass_choice
                case _:
                    return None
        else:
            return None

    def _get_stock_no(
        self,
        stock_data: Optional[TrainStockOutData],
        stock_subclass_data: Optional[TrainStockSubclassOutData],
    ) -> Optional[int]:
        if stock_data is not None and stock_subclass_data is not None:
            return self._get_unit_no_from_input(stock_data)
        return None

    def _get_stock_cars(
        self,
        stock_data: Optional[TrainStockOutData],
        stock_subclass_data: Optional[TrainStockSubclassOutData],
    ) -> Optional[int]:
        if stock_data is not None and stock_subclass_data is not None:
            stock_cars_input = self._get_unit_cars_from_input(
                stock_data, stock_subclass_data
            )
            match stock_cars_input:
                case PickSingle(form):
                    return form
                case _:
                    return None
        return None

    def _get_stock_change_input_reason_string(self, change: StockChange) -> str:
        match change:
            case StockChange.GAIN:
                return "Gain units"
            case StockChange.LOSE:
                return "Lose units"

    def _get_stock_change_reason_from_input(
        self,
        previous_stock_segment: Optional[StockSegment],
    ) -> StockChange:
        if previous_stock_segment is None:
            return StockChange.GAIN
        result = get_choice_from_input(
            "Pick reason for stock change",
            [StockChange.GAIN, StockChange.LOSE],
            display=self._get_stock_change_input_reason_string,
        )
        match result:
            case PickSingle(stock_change):
                return stock_change
            case _:
                raise RuntimeError()

    def _get_stock_from_previous_stock_segment(
        self,
        previous_stock_segment: Optional[StockSegment],
    ) -> list[StockReport]:
        return (
            previous_stock_segment.stock_reports
            if previous_stock_segment is not None
            else []
        )

    def _get_operator_from_service(
        self, service: RttGbnrServiceData
    ) -> Optional[TrainOperatorOutData]:
        operator_code = service.get_operator().code
        if operator_code is None:
            return None
        return select_train_operator_by_operator_code_fetchone(
            self.db_conn,
            operator_code,
            datetime.combine(service.get_run_date(), time(0, 0, 0)),
        )

    def _get_brand_from_input(
        self, operator: TrainOperatorOutData
    ) -> Optional[TrainBrandOutData]:
        if len(operator.operator_brands) == 0:
            return None
        if len(operator.operator_brands) == 1:
            return operator.operator_brands[0]
        match get_choice_from_input(
            "Select brand",
            operator.operator_brands,
            lambda b: f"{b.brand_name} ({b.brand_code})",
        ):
            case PickSingle(brand):
                return brand
            case _:
                return None

    def _get_stock_from_input(
        self,
        calls: list[TrainLegCallInData],
        service: RttGbnrServiceData,
        operator: TrainOperatorOutData,
        brand: Optional[TrainBrandOutData],
        stock_number: int = 0,
    ) -> list[StockSegment]:
        print_information("Recording stock formations")
        stock_segments: list[StockSegment] = []
        previous_stock_segment: Optional[StockSegment] = None
        stock_list = select_train_operator_stock_fetchall(
            self.db_conn,
            operator.operator_id,
            brand.brand_id if brand is not None else None,
            datetime.combine(service.get_run_date(), time(0, 0, 0)),
        )
        current_call = calls[0]
        remaining_calls = calls[1:]
        while len(remaining_calls) > 0:
            print_information(
                f"Recording stock formation after {current_call.station_name}"
            )
            segment_start = current_call
            next_remaining_calls: list[TrainLegCallInData] = []
            stock_end_opt = self._get_call_from_input(
                segment_start, remaining_calls
            )
            if stock_end_opt is None:
                segment_end = remaining_calls[-1]
                segment_end_index = len(calls) - 1
            else:
                _, segment_end_index, next_remaining_calls = stock_end_opt
            stock_calls = [current_call] + remaining_calls[
                0 : segment_end_index + 1
            ]
            remaining_calls = next_remaining_calls
            segment_end = stock_calls[-1]
            stock_change = self._get_stock_change_reason_from_input(
                previous_stock_segment
            )
            previous_stock_segment_stock = (
                self._get_stock_from_previous_stock_segment(
                    previous_stock_segment
                )
            )
            current_segment_stock: list[StockReport] = []
            match stock_change:
                case StockChange.GAIN:
                    number_of_units = get_int_from_input("Number of new units")
                    if number_of_units is None:
                        return []
                    current_segment_stock = previous_stock_segment_stock.copy()
                    for i in range(0, number_of_units):
                        print_information(f"Selecting unit {i + 1}")
                        stock_report = self._get_unit_report_from_input(
                            stock_list
                        )
                        if stock_report is None:
                            return []
                        current_segment_stock.append(stock_report)
                case StockChange.LOSE:
                    result = get_choices_from_input(
                        "Which units remain",
                        previous_stock_segment_stock,
                        string_of_stock_report,
                    )
                    match result:
                        case None:
                            return []
                        case PickMultiple(choices):
                            current_segment_stock = choices
            stock_mileage = self._get_mileage_from_input(stock_calls)
            segment_start_call = stock_calls[0]
            segment_end_call = stock_calls[-1]
            if (
                segment_start_call.dep_call is None
                or segment_end_call.arr_call is None
            ):
                raise RuntimeError("Could not get segment endpoints")
            segment = StockSegment(
                current_segment_stock,
                service.get_identity(),
                datetime.combine(service.get_run_date(), time(0, 0, 0)),
                segment_start_call,
                segment_end_call,
                stock_mileage,
            )
            stock_segments.append(segment)
            previous_stock_segment = segment
            print_information(
                f"Stock formation {len(stock_segments) + stock_number} recorded"
            )
            current_call = segment_end
        return stock_segments

    def _get_mileage_from_input(
        self, calls: list[TrainLegCallInData]
    ) -> Decimal:
        end_mileage = calls[-1].mileage
        if end_mileage is not None:
            return end_mileage
        print_information(
            f"Manual mileage input between {calls[0].station_name} and {calls[-1].station_name} required"
        )
        miles = get_int_from_input("Miles")
        chains = get_int_from_input("Chains", upper=79)
        if miles is None or chains is None:
            raise RuntimeError("Cannot be None")
        return miles_and_chains_to_miles(miles, chains)

    def _get_calls_at_station(
        self, service: RttGbnrServiceData, station_crs: str
    ) -> list[RttGbnrServiceLocation]:
        matching_calls: list[RttGbnrServiceLocation] = []
        for location in service.locations:
            if location.get_crs() == station_crs:
                matching_calls.append(location)
        return matching_calls

    def _get_service_graph_segment_from_input(
        self,
        service_graph: ServiceGraphNode,
        board_station_crs: str,
        board_station_plan_dep: datetime,
        alight_station_crs: str,
    ) -> Optional[list[ServiceGraphNode]]:
        service_graph_segments = get_service_graph_segments(
            service_graph,
            board_station_crs,
            board_station_plan_dep,
            alight_station_crs,
        )
        if not service_graph_segments:
            return None
        if len(service_graph_segments) == 1:
            return service_graph_segments[0]
        choices = list(enumerate(service_graph_segments, start=1))
        result = get_choice_from_input(
            "Select alighting call",
            choices,
            display=self._display_service_graph_segment,
        )
        match result:
            case PickSingle((_, segment)):
                return segment
            case _:
                return None

    def _display_service_graph_segment(
        self,
        choice: tuple[int, list[ServiceGraphNode]],
    ) -> str:
        index, segment = choice
        station_codes = [
            (
                node.location.shortCodes[0]
                if node.location.shortCodes
                else node.location.description or "Unknown"
            )
            for node in segment
        ]
        previous_node = segment[-2]
        arrival = next(
            (
                parent.plan_arr
                for parent in segment[-1].parents
                if parent.node is previous_node
            ),
            None,
        )
        arrival_string = (
            arrival.strftime("%H:%M") if arrival is not None else "unknown"
        )
        return (
            f"Call {index}: {' to '.join(station_codes)} "
            f"(arrives {arrival_string})"
        )

    def _get_leg_calls_from_service_graph_segment(
        self, service_graph_segment: list[ServiceGraphNode]
    ) -> list[TrainLegCallInData]:
        leg_calls: list[TrainLegCallInData] = []
        for index, node in enumerate(service_graph_segment):
            previous_node = (
                service_graph_segment[index - 1] if index > 0 else None
            )
            next_node = (
                service_graph_segment[index + 1]
                if index + 1 < len(service_graph_segment)
                else None
            )
            incoming_relation = self._get_relation_for_graph_node(
                node.parents, previous_node, "incoming"
            )
            outgoing_relation = self._get_relation_for_graph_node(
                node.children, next_node, "outgoing"
            )
            arr_call = (
                self._get_service_call_at_graph_node(
                    node, incoming_relation.service
                )
                if incoming_relation is not None
                else None
            )
            dep_call = (
                self._get_service_call_at_graph_node(
                    node, outgoing_relation.service
                )
                if outgoing_relation is not None
                else None
            )
            short_codes = node.location.shortCodes
            if not short_codes:
                raise RuntimeError("shortCodes missing from graph location")
            if node.location.description is None:
                raise RuntimeError("description missing from graph location")
            association_type = (
                outgoing_relation.association_type
                if outgoing_relation is not None
                and outgoing_relation.association_type is not None
                else (
                    incoming_relation.association_type
                    if incoming_relation is not None
                    else None
                )
            )
            leg_call = TrainLegCallInData(
                short_codes[0],
                node.location.description,
                arr_call,
                dep_call,
                None,
                (
                    get_rtt_association_type_db_int(association_type)
                    if association_type is not None
                    else None
                ),
            )
            leg_calls.append(leg_call)
        return leg_calls

    def _get_relation_for_graph_node(
        self,
        relations: Sequence[
            ServiceGraphParentRelation | ServiceGraphChildRelation
        ],
        adjacent_node: Optional[ServiceGraphNode],
        direction: str,
    ) -> Optional[ServiceGraphParentRelation | ServiceGraphChildRelation]:
        if adjacent_node is None:
            return None
        matching_relations = [
            relation for relation in relations if relation.node is adjacent_node
        ]
        if not matching_relations:
            raise RuntimeError(
                f"Call tree segment is missing an {direction} relation"
            )
        if len(matching_relations) > 1:
            raise RuntimeError(f"Ambiguous {direction} relations")
        return matching_relations[0]

    def _get_service_call_at_graph_node(
        self, node: ServiceGraphNode, service: RttGbnrServiceData
    ) -> TrainLegCallCallInData:
        service_identity = service.get_unique_identity()
        parent_relations = [
            parent
            for parent in node.parents
            if parent.service.get_unique_identity() == service_identity
        ]
        child_relations = [
            child
            for child in node.children
            if child.service.get_unique_identity() == service_identity
        ]
        if len(parent_relations) > 1 or len(child_relations) > 1:
            raise RuntimeError(
                f"Ambiguous {service_identity} call at "
                f"{node.location.description}"
            )
        parent = parent_relations[0] if parent_relations else None
        child = child_relations[0] if child_relations else None
        return TrainLegCallCallInData(
            service.get_identity(),
            datetime.combine(service.get_run_date(), time(0, 0, 0)),
            parent.plan_arr if parent is not None else None,
            parent.act_arr if parent is not None else None,
            child.plan_dep if child is not None else None,
            child.act_dep if child is not None else None,
        )

    @staticmethod
    def _get_multiple_short_station_string(
        locs: list[RttLocationPair],
    ) -> str:
        string = ""
        for i, loc in enumerate(locs):
            station_name = (
                loc.location.description
                if loc.location is not None
                and loc.location.description is not None
                else "Unknown"
            )
            if i == 0:
                string = station_name
            else:
                string = f"{string} and {station_name}"
        return string

    def _get_service_from_service_id_input(
        self,
        run_date: date,
    ) -> Optional[RttGbnrServiceData]:
        result = None
        while result is None:
            service_id = get_text_from_input("Service id")
            if service_id is None:
                return None
            result = (
                self.rtt_gbnr_client.get_service_by_identity_and_departure_date(
                    service_id, run_date
                )
            )
            return result.service
        return None

    def _get_service_from_service_at_station_input(
        self,
        service_at_station: RttGbnrLocationService,
        run_date: date,
    ) -> Optional[RttGbnrServiceData]:
        identity = service_at_station.get_identity()
        run_date = service_at_station.get_run_date()
        return self.rtt_gbnr_client.get_service_by_identity_and_departure_date(
            identity, run_date
        ).service

    def _string_of_departure(self, location: RttGbnrServiceLocation) -> str:
        dep_time = None
        if (plan_dep := location.get_plan_dep()) is not None:
            dep_time = plan_dep
        else:
            dep_time = location.get_act_dep()
        if dep_time is not None:
            time_string = dep_time.strftime("%H:%M")
        else:
            time_string = ""
        if location.get_platform() is not None:
            platform_string = " - Platform {call.platform}"
        else:
            platform_string = ""

        return f"{time_string}{platform_string}"

    def _get_train_leg_service_from_rtt_service(
        self,
        service: RttGbnrServiceData,
        operator: TrainOperatorOutData,
        brand: Optional[TrainBrandOutData],
    ) -> TrainLegServiceInData:
        return TrainLegServiceInData(
            service.get_identity(),
            datetime.combine(service.get_run_date(), time(0, 0, 0)),
            service.get_headcode(),
            operator.operator_id,
            brand.brand_id if brand is not None else None,
            None,
        )

    def _get_train_leg_service_endpoints_from_rtt_service(
        self,
        service: RttGbnrServiceData,
    ) -> list[TrainLegServiceEndpointInData]:
        train_leg_service_endpoints: list[TrainLegServiceEndpointInData] = []
        service_identity = service.get_identity()
        service_run_date = datetime.combine(
            service.get_run_date(), time(0, 0, 0)
        )
        for origin in service.origin:
            train_leg_service_endpoints.append(
                TrainLegServiceEndpointInData(
                    service_identity,
                    service_run_date,
                    origin.get_description(),
                    True,
                )
            )
        for destination in service.destination:
            train_leg_service_endpoints.append(
                TrainLegServiceEndpointInData(
                    service_identity,
                    service_run_date,
                    destination.get_description(),
                    False,
                )
            )
        return train_leg_service_endpoints

    def _get_train_leg_service_calls_from_rtt_service(
        self,
        service: RttGbnrServiceData,
    ) -> list[TrainLegServiceCallInData]:
        service_identity = service.get_identity()
        service_run_date = datetime.combine(
            service.get_run_date(), time(0, 0, 0)
        )
        return [
            TrainLegServiceCallInData(
                service_identity,
                service_run_date,
                location.get_crs(),
                location.get_platform(),
                location.get_plan_arr(),
                location.get_act_arr(),
                location.get_plan_dep(),
                location.get_act_dep(),
                None,
            )
            for location in service.locations
        ]

    def _get_train_leg_service_associations_from_rtt_service(
        self,
        service: RttGbnrServiceData,
    ) -> list[TrainLegAssociatedServiceInData]:
        service_identity = service.get_identity()
        service_run_date = datetime.combine(
            service.get_run_date(), time(0, 0, 0)
        )
        train_leg_service_associations: list[
            TrainLegAssociatedServiceInData
        ] = []
        for location in service.locations:
            for associated_service in location.associatedServices:
                train_leg_service_associations.append(
                    TrainLegAssociatedServiceInData(
                        service_identity,
                        service_run_date,
                        location.get_crs(),
                        location.get_plan_arr(),
                        location.get_act_arr(),
                        location.get_plan_dep(),
                        location.get_act_dep(),
                        associated_service.get_identity(),
                        datetime.combine(
                            associated_service.get_run_date(), time(0, 0, 0)
                        ),
                        get_rtt_association_type_db_int(
                            associated_service.get_association_type()
                        ),
                    )
                )
        return train_leg_service_associations

    def _get_train_in_data_from_rtt_services(
        self,
        services: list[RttGbnrServiceData],
        operator: TrainOperatorOutData,
        brand: Optional[TrainBrandOutData],
    ) -> tuple[
        list[TrainLegServiceInData],
        list[TrainLegServiceEndpointInData],
        list[TrainLegServiceCallInData],
        list[TrainLegAssociatedServiceInData],
    ]:
        train_leg_services = [
            self._get_train_leg_service_from_rtt_service(
                service, operator, brand
            )
            for service in services
        ]
        train_leg_service_endpoints = [
            endpoint
            for service in services
            for endpoint in self._get_train_leg_service_endpoints_from_rtt_service(
                service
            )
        ]
        train_leg_service_calls = [
            call
            for service in services
            for call in self._get_train_leg_service_calls_from_rtt_service(
                service
            )
        ]
        train_leg_service_associations = [
            assoc
            for service in services
            for assoc in self._get_train_leg_service_associations_from_rtt_service(
                service
            )
        ]
        return (
            train_leg_services,
            train_leg_service_endpoints,
            train_leg_service_calls,
            train_leg_service_associations,
        )

    def _get_train_stock_segment_in_data_from_stock_segments(
        self,
        stock_segments: list[StockSegment],
    ) -> list[TrainLegStockSegmentInData]:
        train_stock_segments: list[TrainLegStockSegmentInData] = []
        for stock_segment in stock_segments:
            for stock_report in stock_segment.stock_reports:
                if (
                    stock_segment.start_call.dep_call is None
                    or stock_segment.end_call.arr_call is None
                ):
                    continue
                train_stock_segments.append(
                    TrainLegStockSegmentInData(
                        stock_report.class_no,
                        stock_report.subclass_no,
                        stock_report.stock_no,
                        stock_report.cars,
                        stock_segment.start_call.dep_call.service_uid,
                        stock_segment.start_call.dep_call.service_run_date,
                        stock_segment.start_call.station_crs,
                        stock_segment.start_call.dep_call.plan_dep,
                        stock_segment.start_call.dep_call.act_dep,
                        stock_segment.end_call.arr_call.service_uid,
                        stock_segment.end_call.arr_call.service_run_date,
                        stock_segment.end_call.station_crs,
                        stock_segment.end_call.arr_call.plan_arr,
                        stock_segment.end_call.arr_call.act_arr,
                        stock_segment.mileage,
                    )
                )
        return train_stock_segments

    def _get_train_leg_from_input(
        self,
        start: datetime | None = None,
        default_station: TrainStationOutData | None = None,
    ) -> TrainLegInData | None:
        board_station = self._get_station_from_input("Board", default_station)
        if board_station is None:
            print_error("Could not get board station")
            return None
        alight_station = self._get_station_from_input("Destination")
        if alight_station is None:
            print_error("Could not get destination station")
            return None
        search_datetime = get_datetime_from_input(start)
        if search_datetime is None:
            print_error("Could not get search datetime")
            return None
        service_at_station = self._get_service_at_station_from_input(
            board_station, search_datetime, alight_station
        )
        if service_at_station is None:
            service = self._get_service_from_service_id_input(search_datetime)
            if service is None:
                return None
            service_calls_at_origin = self._get_calls_at_station(
                service, board_station.station_crs
            )
            if len(service_calls_at_origin) == 0:
                print_error(
                    f"No call at {board_station.station_name} found on service"
                )
                return None
            if len(service_calls_at_origin) > 1:
                origin_call_result = get_choice_from_input(
                    "Select boarding call",
                    service_calls_at_origin,
                    self._string_of_departure,
                )
                match origin_call_result:
                    case PickSingle(call):
                        origin_call = call
                    case _:
                        return None
            else:
                origin_call = service_calls_at_origin[0]
            if (plan_dep := origin_call.get_plan_dep()) is None:
                print_error("Could not get planned departure time for service")
                return None
            leg_plan_dep = plan_dep
        else:
            if (plan_dep := service_at_station.get_plan_dep()) is None:
                print_error("Could not get planned departure time for service")
                return None
            service = self._get_service_from_service_at_station_input(
                service_at_station, search_datetime
            )
            if service is None:
                print_error("Could not get service")
                return None
            leg_plan_dep = plan_dep
        services_dict = get_services_dict_from_service(
            service, self.rtt_gbnr_client
        )
        service_graph = build_service_graph(service, services_dict)
        if service_graph is None:
            print_error(
                f"Could not find route between {board_station.station_name} and {alight_station.station_name}"
            )
            return None
        service_graph_segment = self._get_service_graph_segment_from_input(
            service_graph,
            board_station.station_crs,
            leg_plan_dep,
            alight_station.station_crs,
        )
        if service_graph_segment is None:
            print_error(
                f"Could not find route between {board_station.station_name} and {alight_station.station_name}"
            )
            return None
        leg_calls = self._get_leg_calls_from_service_graph_segment(
            service_graph_segment
        )
        operator = self._get_operator_from_service(service)
        if operator is None:
            print_error("Could not get operator")
            return None
        brand = self._get_brand_from_input(operator)
        stock_segments = self._get_stock_from_input(
            leg_calls, service, operator, brand
        )
        mileage = self._get_mileage_from_input(leg_calls)
        print_information(
            f"Computed mileage as {string_of_miles_and_chains(mileage)}"
        )
        if leg_calls[0].mileage is None:
            leg_calls[0].mileage = Decimal(0)
        if leg_calls[-1].mileage is None:
            leg_calls[-1].mileage = mileage
        (
            train_leg_services,
            train_leg_service_endpoints,
            train_leg_service_calls,
            train_leg_service_associations,
        ) = self._get_train_in_data_from_rtt_services(
            list(services_dict.values()), operator, brand
        )
        train_leg_stock_segments = (
            self._get_train_stock_segment_in_data_from_stock_segments(
                stock_segments
            )
        )
        leg = TrainLegInData(
            train_leg_services,
            train_leg_service_endpoints,
            train_leg_service_calls,
            train_leg_service_associations,
            leg_calls,
            train_leg_stock_segments,
            mileage,
        )
        return leg


if __name__ == "__main__":
    with connect_with_env() as db_conn:
        register_types(db_conn)
        rtt_client = RttApiClient()
        rtt_api_manager = RttApiManager(rtt_client)
        rtt_gbnr_client = RttGbnrClient(
            rtt_api_manager.get_access_token().token
        )
        recorder = TrainRecorder(db_conn, rtt_gbnr_client)
        recorder.record_train_leg()
