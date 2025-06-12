from api.db.train.select.service import (
    ShortAssociatedService,
    ShortTrainService,
)
from api.db.train.stations import TrainLegCallStationInData
import folium

from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from networkx import MultiDiGraph
from psycopg import Connection
from pathlib import Path
from typing import Optional
from pydantic import Field
from shapely import LineString, Point

from api.utils.database import connect_with_env
from api.db.train.leg import (
    ShortLeg,
    ShortLegCall,
    ShortLegSegment,
    TrainLegCallStockreportInData,
    get_operator_colour_from_leg,
    select_legs,
)
from api.db.train.points import (
    StationPoint,
    get_station_points_from_crses,
    get_station_points_from_names,
)
from api.network.network import (
    get_node_id_from_station_point,
    merge_linestrings,
)
from api.network.pathfinding import (
    find_shortest_path_between_stations,
    get_linestring_for_leg,
)


@dataclass
class MapPoint:
    point: Point
    colour: str
    size: int
    tooltip: str


@dataclass
class LegLine:
    board_station: str
    alight_station: str
    calls: list[StationPoint]
    points: LineString
    colour: str
    count_lr: int
    count_rl: int


def add_call_marker(
    call: StationPoint,
    colour: str,
    text: str,
    group: Optional[folium.FeatureGroup] = None,
):
    marker = folium.Marker(
        location=[call.point.y, call.point.x],
        tooltip=text,
        icon=folium.Icon(color=colour, icon="train", prefix="fa"),
    )
    if group is not None:
        group.add_child(marker)


@dataclass
class CallInfo:
    pass


@dataclass
class StationInfo:
    include_counts: bool


type MarkerTextType = CallInfo | StationInfo


@dataclass
class StationCount:
    board: int
    call: int
    alight: int


@dataclass
class BoardCount:
    pass


@dataclass
class CallCount:
    pass


@dataclass
class AlightCount:
    pass


type CountType = BoardCount | CallCount | AlightCount

type StationCountDict = dict[str, tuple[StationPoint, StationCount]]


def update_station_count_dict(
    station_count_dict: StationCountDict,
    station_point: StationPoint,
    update_type: CountType,
) -> StationCountDict:
    current_station = station_count_dict.get(station_point.crs)
    if current_station is None:
        current_station_count = StationCount(0, 0, 0)
    else:
        (_, current_station_count) = station_count_dict[station_point.crs]
    current_board = current_station_count.board
    current_call = current_station_count.call
    current_alight = current_station_count.alight
    match update_type:
        case BoardCount():
            new_station_count = StationCount(
                current_board + 1, current_call, current_alight
            )
        case CallCount():
            new_station_count = StationCount(
                current_board, current_call + 1, current_alight
            )
        case AlightCount():
            new_station_count = StationCount(
                current_board, current_call, current_alight + 1
            )
    station_count_dict[station_point.crs] = (station_point, new_station_count)
    return station_count_dict


def get_call_info_time_string(call_time: Optional[datetime]) -> str:
    if call_time is None:
        return "--"
    return f"{call_time.strftime("%H%M")}"


def get_call_info_text(station_point: StationPoint) -> str:
    if station_point.call is None:
        time_string = ""
    else:
        plan_arr_str = get_call_info_time_string(station_point.call.plan_arr)
        plan_dep_str = get_call_info_time_string(station_point.call.plan_dep)
        act_arr_str = get_call_info_time_string(station_point.call.act_arr)
        act_dep_str = get_call_info_time_string(station_point.call.act_dep)
        arr_string = f"<b>arr</b> plan {plan_arr_str} act {act_arr_str}"
        dep_string = f"<b>dep</b> plan {plan_dep_str} act {act_dep_str}"
        time_string = f"{arr_string}<br/>{dep_string}"
    return f"<h1>{station_point.name} ({station_point.crs})</h1>{time_string}"


def get_station_info_text(
    station_point: StationPoint,
    include_counts: bool,
    boards: int,
    calls: int,
    alights: int,
) -> str:
    if include_counts:
        count_string = f"""
                <b>Boards:</b> {boards}<br/>
                <b>Alights:</b> {alights}<br/>
                <b>Calls:</b> {calls}
            """
    else:
        count_string = ""
    return f"<h1>{station_point.name} ({station_point.crs})</h1>{count_string}"


def get_leg_map(
    map_points: list[MapPoint],
    leg_lines: list[LegLine],
    text_type: MarkerTextType,
) -> str:
    m = folium.Map(
        tiles=None,
        location=(53.906602, -1.933667),
        zoom_start=6,
    )
    folium.TileLayer(
        "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="Map",
    ).add_to(m)
    station_count_dict = {}
    line_group = folium.FeatureGroup(name="Legs")
    for map_point in map_points:
        folium.Circle(
            location=[map_point.point.y, map_point.point.x],
            radius=map_point.size,
            color=map_point.colour,
            fill=True,
            opacity=1,
            tooltip=map_point.tooltip,
        ).add_to(m)
    for leg_line in leg_lines:
        tooltip = f"{leg_line.board_station} to {leg_line.alight_station}"
        line = folium.PolyLine(
            locations=[
                (point[1], point[0]) for point in leg_line.points.coords
            ],
            color=leg_line.colour,
            tooltip=tooltip,
            weight=4,
        )
        line_group.add_child(line)
        station_count_dict = update_station_count_dict(
            station_count_dict, leg_line.calls[0], BoardCount()
        )
        for call in leg_line.calls[1:-2]:
            station_count_dict = update_station_count_dict(
                station_count_dict, call, CallCount()
            )
        station_count_dict = update_station_count_dict(
            station_count_dict, leg_line.calls[-1], AlightCount()
        )
    line_group.add_to(m)
    endpoint_group = folium.FeatureGroup(name="Endpoints")
    call_group = folium.FeatureGroup(name="Calls")
    for station_count_key in station_count_dict.keys():
        (station_point, station_count) = station_count_dict[station_count_key]
        boards = station_count.board
        calls = station_count.call
        alights = station_count.alight
        match text_type:
            case StationInfo(include_counts):
                text = get_station_info_text(
                    station_point, include_counts, boards, calls, alights
                )
            case CallInfo():
                text = get_call_info_text(station_point)
        if station_count.call > 0:
            add_call_marker(station_point, "green", text, call_group)
        if boards > 0 or alights > 0:
            add_call_marker(station_point, "blue", text, endpoint_group)

    call_group.add_to(m)
    endpoint_group.add_to(m)
    folium.LayerControl().add_to(m)
    return m.get_root().render()


def get_leg_map_from_gml(gml_data: BeautifulSoup) -> str:
    geometry_key = gml_data.find_all("key", {"attr.name": "geometry"})
    geometry_attribute = geometry_key[0]["id"]
    lat_key = gml_data.find_all("key", {"attr.name": "y"})
    lat_attribute = lat_key[0]["id"]
    lon_key = gml_data.find_all("key", {"attr.name": "x"})
    lon_attribute = lon_key[0]["id"]
    nodes = gml_data.find_all("node")
    node_dict = {}
    for node in nodes:
        node_id = node.get("id")
        node_lat = node.find("data", {"key": lat_attribute}).text
        node_lon = node.find("data", {"key": lon_attribute}).text
        node_dict[node_id] = (Decimal(node_lat), Decimal(node_lon))

    edges = gml_data.find_all("edge")

    leg_lines = []

    for edge in edges:
        edge_source = edge.get("source")
        edge_target = edge.get("target")

        (source_lat, source_lon) = node_dict[edge_source]
        (target_lat, target_lon) = node_dict[edge_target]

        edge_nodes = [Point(source_lon, source_lat)]

        intermediate_nodes = edge.find("data", {"key": geometry_attribute})
        edge_nodes.append(Point(source_lon, source_lat))
        if intermediate_nodes is not None:
            linestring_text = intermediate_nodes.text
            node_string_list = linestring_text[12:-1].split(", ")
            for node_string in node_string_list:
                node_points = node_string.split(" ")
                edge_nodes.append(
                    Point(float(node_points[0]), float(node_points[1]))
                )
        edge_nodes.append(Point(target_lon, target_lat))

        leg_line = LegLine(
            "",
            "",
            [],
            LineString(edge_nodes),
            "#000000",
            0,
            0,
        )
        leg_lines.append(leg_line)
    return get_leg_map([], leg_lines, StationInfo(False))


def get_leg_map_from_gml_file(leg_file: str | Path) -> str:
    with open(leg_file, "r") as f:
        data = f.read()
    xml_data = BeautifulSoup(data, "xml")
    return get_leg_map_from_gml(xml_data)


def get_leg_line_for_leg(
    network: MultiDiGraph,
    leg: ShortLeg,
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> Optional[LegLine]:
    result = get_linestring_for_leg(network, leg.calls, station_points)
    if result is None:
        return None
    (station_list, path_list) = result
    return LegLine(
        leg.calls[0].station.name,
        leg.calls[-1].station.name,
        station_list,
        path_list,
        get_operator_colour_from_leg(leg),
        0,
        0,
    )


def get_leg_line_for_leg_calls(
    network: MultiDiGraph,
    leg_data: list[ShortLegCall],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> Optional[LegLine]:
    previous_call = leg_data[0]
    paths = []
    for call in leg_data[1:]:
        result = find_shortest_path_between_stations(
            network,
            previous_call.station.crs,
            None,
            call.station.crs,
            None,
            station_points,
        )
        if result is None:
            return None
        paths.append(result)
        previous_call = call

    line_strings = [path for (_, _, path) in paths]
    complete_line = merge_linestrings(line_strings)
    leg_line = LegLine(
        leg_data[0].station.name,
        leg_data[-1].station.name,
        [paths[0][0], paths[-1][1]],
        complete_line,
        "#000000",
        0,
        0,
    )
    return leg_line


def get_leg_lines_for_leg_data(
    network: MultiDiGraph,
    legs: list[list[ShortLegCall]],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> list[LegLine]:
    leg_lines: list[LegLine] = []
    for leg in legs:
        leg_line = get_leg_line_for_leg_calls(network, leg, station_points)
        if leg_line is not None:
            leg_lines.append(leg_line)
    return leg_lines


def get_leg_lines_for_legs(
    network: MultiDiGraph,
    legs: list[ShortLeg],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> list[LegLine]:
    leg_strings = []
    for leg in legs:
        leg_string = get_leg_line_for_leg(network, leg, station_points)
        if leg_string is not None:
            leg_strings.append(leg_string)
    return leg_strings


def get_leg_map_page(
    network: MultiDiGraph,
    conn: Connection,
    user_id: int,
    text_type: MarkerTextType,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
    search_leg_id: Optional[int] = None,
) -> str:
    legs = select_legs(conn, user_id, search_start, search_end, search_leg_id)
    stations = []
    for leg in legs:
        for call in leg.calls:
            stations.append((call.station.crs, call.platform))
    station_points = get_station_points_from_crses(conn, stations)
    leg_lines = get_leg_lines_for_legs(network, legs, station_points)
    html = get_leg_map([], leg_lines, text_type)
    return html


@dataclass
class LegData:
    board_station: str = Field(alias="from")
    alight_station: str = Field(alias="to")
    via: Optional[list[str]] = None


def get_leg_map_page_from_leg_data(
    network: MultiDiGraph, legs: list[LegData]
) -> str:
    stations = set()
    for leg in legs:
        stations.add((leg.board_station, None))
        stations.add((leg.alight_station, None))
        if leg.via is not None:
            for via_station in leg.via:
                stations.add((via_station, None))
    with connect_with_env() as conn:
        (name_to_station_dict, station_points) = get_station_points_from_names(
            conn, list(stations)
        )
    base_leg_data: list[list[ShortLegCall]] = []
    for leg in legs:
        board_station = name_to_station_dict[leg.board_station]
        alight_station = name_to_station_dict[leg.alight_station]
        calls = [
            ShortLegCall(
                board_station, None, None, None, None, None, None, [], None
            )
        ]
        if leg.via is not None:
            for via_station in leg.via:
                call_station = name_to_station_dict[via_station]
                calls.append(
                    ShortLegCall(
                        call_station,
                        None,
                        None,
                        None,
                        None,
                        None,
                        [],
                        None,
                        None,
                    )
                )
        calls.append(
            ShortLegCall(
                alight_station, None, None, None, None, None, [], None, None
            )
        )
        base_leg_data.append(calls)

    leg_lines = get_leg_lines_for_leg_data(
        network, base_leg_data, station_points
    )
    html = get_leg_map([], leg_lines, StationInfo(True))
    return html


@dataclass
class ShortLegCallWithGeometry:
    station: TrainLegCallStationInData
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    associated_service: Optional[list[ShortAssociatedService]]
    leg_stock: Optional[list[TrainLegCallStockreportInData]]
    mileage: Optional[Decimal]
    point: Optional[tuple[Decimal, Decimal]]


def short_leg_call_to_short_leg_call_with_geometry(
    leg_call: ShortLegCall,
) -> ShortLegCallWithGeometry:
    return ShortLegCallWithGeometry(
        leg_call.station,
        leg_call.platform,
        leg_call.plan_arr,
        leg_call.plan_dep,
        leg_call.act_arr,
        leg_call.act_dep,
        leg_call.associated_service,
        leg_call.leg_stock,
        leg_call.mileage,
        None,
    )


@dataclass
class ShortLegWithGeometry:
    id: int
    user_id: int
    leg_start: datetime
    services: dict[str, ShortTrainService]
    calls: list[ShortLegCallWithGeometry]
    stocks: list[ShortLegSegment]
    distance: Optional[Decimal]
    duration: Optional[timedelta]
    geometry: Optional[list[tuple[Decimal, Decimal]]]


def short_leg_to_short_leg_with_geometry(leg: ShortLeg) -> ShortLegWithGeometry:
    return ShortLegWithGeometry(
        leg.id,
        leg.user_id,
        leg.leg_start,
        leg.services,
        [
            short_leg_call_to_short_leg_call_with_geometry(leg_call)
            for leg_call in leg.calls
        ],
        leg.stocks,
        leg.distance,
        leg.duration,
        None,
    )


def short_legs_to_short_legs_with_geometries(
    legs: list[ShortLeg],
) -> list[ShortLegWithGeometry]:
    return [short_leg_to_short_leg_with_geometry(leg) for leg in legs]


def get_short_leg_with_geometry(
    network: MultiDiGraph,
    leg: ShortLeg,
    station_points: dict[str, dict[str | None, StationPoint]],
) -> ShortLegWithGeometry:
    result = get_linestring_for_leg(network, leg.calls, station_points)
    if result is None:
        coords = None
        calls_with_geometry = [
            short_leg_call_to_short_leg_call_with_geometry(leg_call)
            for leg_call in leg.calls
        ]
    else:
        (points, line_string) = result
        coords = [
            (Decimal(coord[0]), Decimal(coord[1]))
            for coord in line_string.coords
        ]
        calls_with_geometry = []
        for i, leg_call in enumerate(leg.calls):
            station_point = points[i]
            station_point_id = get_node_id_from_station_point(station_point)
            station_node = network.nodes[station_point_id]
            calls_with_geometry.append(
                ShortLegCallWithGeometry(
                    leg_call.station,
                    leg_call.platform,
                    leg_call.plan_arr,
                    leg_call.plan_dep,
                    leg_call.act_arr,
                    leg_call.act_dep,
                    leg_call.associated_service,
                    leg_call.leg_stock,
                    leg_call.mileage,
                    (
                        Decimal(station_node["x"]),
                        Decimal(station_node["y"]),
                    ),
                )
            )
    return ShortLegWithGeometry(
        leg.id,
        leg.user_id,
        leg.leg_start,
        leg.services,
        calls_with_geometry,
        leg.stocks,
        leg.distance,
        leg.duration,
        coords,
    )


def get_short_legs_with_geometries(
    conn: Connection, network: MultiDiGraph, legs: list[ShortLeg]
) -> list[ShortLegWithGeometry]:
    stations: set[tuple[str, Optional[str]]] = set()
    for leg in legs:
        for call in leg.calls:
            stations.add((call.station.crs, call.platform))
    station_points = get_station_points_from_crses(conn, list(stations))
    legs_with_geometries: list[ShortLegWithGeometry] = []
    for leg in legs:
        legs_with_geometries.append(
            get_short_leg_with_geometry(network, leg, station_points)
        )
    return legs_with_geometries
