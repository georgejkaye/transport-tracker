import json
import folium

from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from networkx import MultiDiGraph
from psycopg import Connection
from pathlib import Path
from typing import Optional
from pydantic import Field
from shapely import LineString, Point

from api.data.database import connect
from api.data.stations import (
    StationPoint,
    get_station_points_from_crses,
    get_station_points_from_names,
)
from api.api.network import network
from api.data.leg import ShortLeg, get_operator_colour_from_leg, select_legs
from api.data.network import (
    find_shortest_path_between_stations,
    get_linestring_for_leg,
    insert_node_dict_to_network,
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
    points: LineString
    colour: str
    count_lr: int
    count_rl: int


def make_leg_map(map_points: list[MapPoint], leg_lines: list[LegLine]) -> str:
    m = folium.Map(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        location=(53.906602, -1.933667),
        zoom_start=6,
    )
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
        folium.PolyLine(
            locations=[
                (point[1], point[0]) for point in leg_line.points.coords
            ],
            color=leg_line.colour,
            tooltip=tooltip,
            weight=4,
        ).add_to(m)
    return m.get_root().render()


def make_leg_map_from_gml(gml_data: BeautifulSoup) -> str:
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
            LineString(edge_nodes),
            "#000000",
            0,
            0,
        )
        leg_lines.append(leg_line)
    return make_leg_map([], leg_lines)


def make_leg_map_from_gml_file(leg_file: str | Path) -> str:
    with open(leg_file, "r") as f:
        data = f.read()
    xml_data = BeautifulSoup(data, "xml")
    return make_leg_map_from_gml(xml_data)


def get_leg_line(
    network: MultiDiGraph,
    leg: ShortLeg,
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> Optional[LegLine]:
    linestring = get_linestring_for_leg(network, leg, station_points)
    if linestring is None:
        return None
    return LegLine(
        leg.calls[0].station.name,
        leg.calls[-1].station.name,
        linestring,
        get_operator_colour_from_leg(leg),
        0,
        0,
    )


@dataclass
class BaseLegData:
    board_crs: str
    board_name: str
    alight_crs: str
    alight_name: str


def get_leg_line_for_station_pair(
    network: MultiDiGraph,
    leg_data: BaseLegData,
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> Optional[LegLine]:
    path = find_shortest_path_between_stations(
        network,
        leg_data.board_crs,
        None,
        leg_data.alight_crs,
        None,
        station_points,
    )
    if path is None:
        return None
    leg_line = LegLine(
        leg_data.board_name,
        leg_data.alight_name,
        path,
        "#000000",
        0,
        0,
    )
    return leg_line


def get_leg_lines_for_leg_data(
    network: MultiDiGraph,
    leg_data: list[BaseLegData],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> list[LegLine]:
    leg_lines = []
    for leg in leg_data:
        leg_line = get_leg_line_for_station_pair(network, leg, station_points)
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
        leg_string = get_leg_line(network, leg, station_points)
        if leg_string is not None:
            leg_strings.append(leg_string)
    return leg_strings


def get_leg_map_page(
    network: MultiDiGraph,
    conn: Connection,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
    search_leg_id: Optional[int] = None,
) -> str:
    legs = select_legs(conn, search_start, search_end, search_leg_id)
    stations = []
    for leg in legs:
        for call in leg.calls:
            stations.append((call.station.crs, call.platform))
    station_points = get_station_points_from_crses(conn, stations)
    leg_lines = get_leg_lines_for_legs(network, legs, station_points)
    html = make_leg_map([], leg_lines)
    return html


@dataclass
class LegData:
    board_station: str = Field(alias="from")
    alight_station: str = Field(alias="to")


def get_leg_map_page_from_leg_data(
    network: MultiDiGraph, legs: list[LegData]
) -> str:
    stations = set()
    for leg in legs:
        stations.add((leg.board_station, None))
        stations.add((leg.alight_station, None))
    with connect() as (conn, _):
        (name_to_station_dict, station_points) = get_station_points_from_names(
            conn, list(stations)
        )
    base_leg_data = []
    for leg in legs:
        board_station = name_to_station_dict[leg.board_station]
        alight_station = name_to_station_dict[leg.alight_station]
        base_leg_data.append(
            BaseLegData(
                board_station.crs,
                board_station.name,
                alight_station.crs,
                alight_station.name,
            )
        )

    print(base_leg_data)
    leg_lines = get_leg_lines_for_leg_data(
        network, base_leg_data, station_points
    )
    html = make_leg_map([], leg_lines)
    return html
