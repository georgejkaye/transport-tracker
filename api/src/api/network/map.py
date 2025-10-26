from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable, Optional

import folium
from bs4 import BeautifulSoup, Tag
from networkx import MultiDiGraph
from psycopg import Connection
from pydantic import Field
from shapely import LineString, Point

from api.classes.network.geometry import TrainLegCallGeometry, TrainLegGeometry
from api.classes.network.map import (
    AlightCount,
    BoardCount,
    CallCount,
    CountType,
    LegLine,
    LegLineCall,
    LegLineGeometry,
    MapPoint,
    MarkerTextParams,
    MarkerTextValues,
    StationCount,
    StationCountDict,
)
from api.classes.train.legs import (
    DbTrainLegCallPointPointsOutData,
)
from api.classes.train.station import DbTrainStationPointPointsOutData
from api.db.functions.select.train.leg import (
    select_train_leg_points_by_leg_id_fetchone,
    select_train_leg_points_by_leg_ids_fetchall,
    select_train_leg_points_by_user_id_fetchall,
)
from api.db.functions.select.train.station import (
    select_train_station_leg_points_by_name_lists_fetchall,
)
from api.db.types.train.leg import TrainLegPointsOutData
from api.db.types.train.station import TrainStationLegNamesInData
from api.library.folium import create_polyline, render_map
from api.network.pathfinding import get_leg_line_geometry_for_leg


def add_call_marker(
    call: LegLineCall,
    colour: str,
    text: str,
    group: Optional[folium.FeatureGroup] = None,
) -> None:
    point = call.get_point()
    marker = folium.Marker(
        location=[point.x, point.y],
        tooltip=text,
        icon=folium.Icon(color=colour, icon="train", prefix="fa"),
    )
    if group is not None:
        group.add_child(marker)


def update_call_marker_dict[T: LegLineCall](
    call_marker_dict: StationCountDict[T],
    call: T,
    update_type: CountType,
) -> StationCountDict[T]:
    current_station = call_marker_dict.get(call.get_call_identifier())
    if current_station is None:
        current_station_count = StationCount(0, 0, 0)
    else:
        (_, current_station_count) = call_marker_dict[
            call.get_call_identifier()
        ]
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
    call_marker_dict[call.get_call_identifier()] = (
        call,
        new_station_count,
    )
    return call_marker_dict


def get_leg_map[T: LegLineCall](
    map_points: list[MapPoint],
    leg_lines: list[LegLine[T]],
    marker_text_params: MarkerTextParams,
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
    call_marker_dict: StationCountDict[T] = {}
    line_group = folium.FeatureGroup(name="Legs")
    for map_point in map_points:
        folium.Circle(
            location=[map_point.point.x, map_point.point.y],
            radius=map_point.size,
            color=map_point.colour,
            fill=True,
            opacity=1,
            tooltip=map_point.tooltip,
        ).add_to(m)
    for leg_line in leg_lines:
        tooltip = f"{leg_line.board_station} to {leg_line.alight_station}"
        line = create_polyline(
            locations=[
                (point[1], point[0]) for point in leg_line.points.coords
            ],
            colour=leg_line.colour,
            tooltip=tooltip,
            weight=4,
        )
        line_group.add_child(line)
        call_marker_dict = update_call_marker_dict(
            call_marker_dict, leg_line.calls[0], BoardCount()
        )
        for call in leg_line.calls[1:-1]:
            call_marker_dict = update_call_marker_dict(
                call_marker_dict, call, CallCount()
            )
        call_marker_dict = update_call_marker_dict(
            call_marker_dict, leg_line.calls[-1], AlightCount()
        )
    line_group.add_to(m)
    endpoint_group = folium.FeatureGroup(name="Endpoints")
    call_group = folium.FeatureGroup(name="Calls")
    for station_count_key in call_marker_dict.keys():
        (call_marker, call_count) = call_marker_dict[station_count_key]
        boards = call_count.board
        calls = call_count.call
        alights = call_count.alight
        marker_text_values = MarkerTextValues(boards, calls, alights)
        text = call_marker.get_call_info_text(
            marker_text_params, marker_text_values
        )
        if call_count.call > 0:
            add_call_marker(call_marker, "green", text, call_group)
        if boards > 0 or alights > 0:
            add_call_marker(call_marker, "blue", text, endpoint_group)
    call_group.add_to(m)
    endpoint_group.add_to(m)
    folium.LayerControl().add_to(m)
    return render_map(m)


def get_leg_map_from_gml(gml_data: BeautifulSoup) -> Optional[str]:
    geometry_key = gml_data.find_all("key", {"attr.name": "geometry"})
    geometry_key_id = geometry_key[0]
    if not isinstance(geometry_key_id, Tag):
        return None
    geometry_attribute = geometry_key_id.get("id")
    if not isinstance(geometry_attribute, str):
        return None
    lat_keys = gml_data.find_all("key", {"attr.name": "y"})
    lat_first_key = lat_keys[0]
    if not isinstance(lat_first_key, Tag):
        return None
    lat_attribute = lat_first_key.get("id")
    if lat_attribute is None:
        return None
    lon_keys = gml_data.find_all("key", {"attr.name": "x"})
    lon_first_key = lon_keys[0]
    if not isinstance(lon_first_key, Tag):
        return None
    lon_attribute = lon_first_key.get("id")
    if lon_attribute is None:
        return None
    nodes = gml_data.find_all("node")
    node_dict: dict[str, tuple[Decimal, Decimal]] = {}
    for node in nodes:
        if not isinstance(node, Tag):
            return None
        node_id = node.get("id")
        if not isinstance(node_id, str):
            return None
        node_lat = node.find("data", {"key": lat_attribute})
        if node_lat is None:
            return None
        node_lat_text = node_lat.text
        node_lon = node.find("data", {"key": lon_attribute})
        if node_lon is None:
            return None
        node_lon_text = node_lon.text
        node_dict[node_id] = (Decimal(node_lat_text), Decimal(node_lon_text))

    edges = gml_data.find_all("edge")

    leg_lines: list[LegLine[LegLineCall]] = []

    for edge in edges:
        if not isinstance(edge, Tag):
            return None
        edge_source = edge.get("source")
        edge_target = edge.get("target")

        if (
            edge_source is None
            or edge_target is None
            or not isinstance(edge_source, str)
            or not isinstance(edge_target, str)
        ):
            return None

        (source_lat, source_lon) = node_dict[edge_source]
        (target_lat, target_lon) = node_dict[edge_target]

        edge_nodes = [Point(float(source_lon), float(source_lat))]

        intermediate_nodes = edge.find("data", {"key": geometry_attribute})

        if intermediate_nodes is not None:
            linestring_text = intermediate_nodes.text
            node_string_list = linestring_text[12:-1].split(", ")
            for node_string in node_string_list:
                node_points = node_string.split(" ")
                edge_nodes.append(
                    Point(float(node_points[0]), float(node_points[1]))
                )
        edge_nodes.append(Point(float(target_lon), float(target_lat)))

        calls: list[LegLineCall] = []

        leg_line = LegLine(
            "",
            "",
            calls,
            LineString(edge_nodes),
            "#000000",
            0,
            0,
        )
        leg_lines.append(leg_line)
    return get_leg_map([], leg_lines, MarkerTextParams(False))


def get_leg_map_from_gml_file(leg_file: str | Path) -> Optional[str]:
    with open(leg_file, "r") as f:
        data = f.read()
    xml_data = BeautifulSoup(data, "xml")
    return get_leg_map_from_gml(xml_data)


def get_leg_line_geometry_for_leg_id(
    conn: Connection,
    network: MultiDiGraph[int],
    leg_id: int,
) -> Optional[LegLineGeometry[DbTrainLegCallPointPointsOutData]]:
    leg = select_train_leg_points_by_leg_id_fetchone(conn, leg_id)
    if leg is None:
        return None
    return get_leg_line_geometry_for_leg(
        network,
        [
            [
                DbTrainLegCallPointPointsOutData(call, point)
                for point in call.points
            ]
            for call in leg.call_points
        ],
    )


def get_leg_lines_for_leg_points(
    network: MultiDiGraph[int],
    leg_points: list[TrainLegPointsOutData],
    get_train_operator_brand_colour: Callable[
        [int, Optional[int]], Optional[str]
    ],
) -> list[LegLine[DbTrainLegCallPointPointsOutData]]:
    return [
        LegLine(
            leg.call_points[0].station_name,
            leg.call_points[-1].station_name,
            leg_line_geometry.calls,
            leg_line_geometry.line,
            f"#{get_train_operator_brand_colour(leg.operator_id, leg.brand_id)}",
            1,
            0,
        )
        for leg in leg_points
        if (
            leg_line_geometry := get_leg_line_geometry_for_leg(
                network,
                [
                    [
                        DbTrainLegCallPointPointsOutData(call, point)
                        for point in call.points
                    ]
                    for call in leg.call_points
                ],
            )
        )
        is not None
    ]


def get_train_leg_geometries_for_leg_points(
    network: MultiDiGraph[int],
    leg_points: list[TrainLegPointsOutData],
) -> list[TrainLegGeometry]:
    train_leg_geometries: list[TrainLegGeometry] = []
    for leg in leg_points:
        leg_line_geometry = get_leg_line_geometry_for_leg(
            network,
            [
                [
                    DbTrainLegCallPointPointsOutData(call, point)
                    for point in call.points
                ]
                for call in leg.call_points
            ],
        )
        if leg_line_geometry is None:
            continue
        train_leg_geometry = TrainLegGeometry(
            leg.leg_id,
            leg.operator_id,
            leg.brand_id,
            [
                TrainLegCallGeometry(
                    call.call.station_id,
                    call.call.station_crs,
                    call.call.station_name,
                    call.call.platform,
                    call.call.plan_arr,
                    call.call.act_arr,
                    call.call.plan_dep,
                    call.call.act_dep,
                    call.point.longitude,
                    call.point.latitude,
                )
                for call in leg_line_geometry.calls
            ],
            [
                (Decimal(coord[0]), Decimal(coord[1]))
                for coord in leg_line_geometry.line.coords
            ],
        )
        train_leg_geometries.append(train_leg_geometry)
    return train_leg_geometries


def get_train_leg_geometry_for_leg_points(
    network: MultiDiGraph[int], leg_points: TrainLegPointsOutData
) -> Optional[TrainLegGeometry]:
    legs = get_train_leg_geometries_for_leg_points(network, [leg_points])
    if len(legs) == 0:
        return None
    return legs[0]


def get_leg_lines_for_leg_ids(
    conn: Connection,
    network: MultiDiGraph[int],
    leg_ids: list[int],
    get_train_operator_brand_colour: Callable[
        [int, Optional[int]], Optional[str]
    ],
) -> list[LegLine[DbTrainLegCallPointPointsOutData]]:
    leg_points = select_train_leg_points_by_leg_ids_fetchall(conn, leg_ids)
    return get_leg_lines_for_leg_points(
        network, leg_points, get_train_operator_brand_colour
    )


def get_leg_line_geometries_for_leg_ids(
    conn: Connection,
    network: MultiDiGraph[int],
    leg_ids: list[int],
) -> list[TrainLegGeometry]:
    leg_points = select_train_leg_points_by_leg_ids_fetchall(conn, leg_ids)
    return get_train_leg_geometries_for_leg_points(network, leg_points)


def get_leg_lines_for_user_id(
    conn: Connection,
    network: MultiDiGraph[int],
    user_id: int,
    get_train_operator_brand_colour: Callable[
        [int, Optional[int]], Optional[str]
    ],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[LegLine[DbTrainLegCallPointPointsOutData]]:
    leg_points = select_train_leg_points_by_user_id_fetchall(
        conn, user_id, start_date, end_date
    )
    return get_leg_lines_for_leg_points(
        network, leg_points, get_train_operator_brand_colour
    )


def get_leg_line_geometries_for_user_id(
    conn: Connection,
    network: MultiDiGraph[int],
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[TrainLegGeometry]:
    leg_points = select_train_leg_points_by_user_id_fetchall(
        conn, user_id, start_date, end_date
    )
    return get_train_leg_geometries_for_leg_points(network, leg_points)


def get_leg_lines_for_leg_data(
    conn: Connection, network: MultiDiGraph[int], legs: list[LegData]
) -> list[LegLine[DbTrainStationPointPointsOutData]]:
    station_leg_names: list[list[str]] = []
    for leg in legs:
        station_names: list[str] = []
        station_names.append(leg.board_station)
        if leg.via is not None:
            for via_station in leg.via:
                station_names.append(via_station)
        station_names.append(leg.alight_station)
        station_leg_names.append(station_names)
    leg_station_points = select_train_station_leg_points_by_name_lists_fetchall(
        conn, [TrainStationLegNamesInData(names) for names in station_leg_names]
    )
    return [
        LegLine(
            leg_line.leg_stations[0].station_name,
            leg_line.leg_stations[-1].station_name,
            linestring.calls,
            linestring.line,
            "#000000",
            1,
            0,
        )
        for leg_line in leg_station_points
        if (
            linestring := get_leg_line_geometry_for_leg(
                network,
                [
                    [
                        DbTrainStationPointPointsOutData(station, platform)
                        for platform in station.platform_points
                    ]
                    for station in leg_line.leg_stations
                ],
            )
        )
        is not None
    ]


def get_leg_map_page_by_leg_geometries[T: LegLineCall](
    map_points: list[MapPoint],
    leg_lines: list[LegLine[T]],
    marker_text_params: MarkerTextParams,
) -> str:
    return get_leg_map(map_points, leg_lines, marker_text_params)


def get_leg_map_page_by_leg_ids(
    conn: Connection,
    network: MultiDiGraph[int],
    leg_ids: list[int],
    get_train_operator_brand_colour: Callable[[int, Optional[int]], str],
):
    leg_lines = get_leg_lines_for_leg_ids(
        conn, network, leg_ids, get_train_operator_brand_colour
    )
    return get_leg_map_page_by_leg_geometries([], leg_lines, MarkerTextParams())


def get_leg_map_page_by_leg_id(
    conn: Connection,
    network: MultiDiGraph[int],
    leg_id: int,
    get_train_operator_brand_colour: Callable[
        [int, Optional[int]], Optional[str]
    ],
):
    leg_lines = get_leg_lines_for_leg_ids(
        conn, network, [leg_id], get_train_operator_brand_colour
    )
    return get_leg_map_page_by_leg_geometries(
        [], leg_lines, MarkerTextParams(include_times=True)
    )


def get_leg_map_page_by_user_id(
    network: MultiDiGraph[int],
    conn: Connection,
    user_id: int,
    get_train_operator_brand_colour: Callable[
        [int, Optional[int]], Optional[str]
    ],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> str:
    leg_geometries = get_leg_lines_for_user_id(
        conn,
        network,
        user_id,
        get_train_operator_brand_colour,
        start_date,
        end_date,
    )
    return get_leg_map_page_by_leg_geometries(
        [], leg_geometries, MarkerTextParams(False)
    )


@dataclass
class LegData:
    board_station: str = Field(alias="from")
    alight_station: str = Field(alias="to")
    via: Optional[list[str]] = None


def get_leg_map_page_from_leg_data(
    conn: Connection, network: MultiDiGraph[int], legs: list[LegData]
) -> str:
    leg_geometries = get_leg_lines_for_leg_data(conn, network, legs)
    return get_leg_map_page_by_leg_geometries(
        [], leg_geometries, MarkerTextParams(include_counts=True)
    )
