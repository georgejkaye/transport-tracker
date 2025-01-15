import json
import sys
import folium
import osmnx as ox

from api.data.leg import ShortLeg, get_operator_colour_from_leg, select_legs
from api.data.network import (
    find_path_between_nodes,
    find_path_between_stations,
    insert_node_dict_to_network,
    merge_linestrings,
)
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
    get_station_lonlats_from_names,
    get_station_points_from_names,
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


def get_leg_lines_from_db(
    conn: Connection,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> list[LegLine]:
    rows = conn.execute(
        "SELECT * FROM GetLegLines(%s, %s)", [start_date, end_date]
    ).fetchall()
    leg_dict = {}
    for row in rows:
        board_crs = row[0]
        alight_crs = row[4]
        colour = row[8]
        if leg_dict.get((board_crs, alight_crs)) is not None:
            leg_dict[(board_crs, alight_crs)].count_lr = (
                leg_dict[(board_crs, alight_crs)].count_lr + 1
            )
        elif leg_dict.get((alight_crs, board_crs)) is not None:
            leg_dict[(alight_crs, board_crs)].count_rl = (
                leg_dict[(alight_crs, board_crs)].count_rl + 1
            )
        else:
            leg_dict[(board_crs, alight_crs)] = LegLine(
                row[1],
                row[5],
                LineString([Point(row[2], row[3]), Point(row[6], row[7])]),
                row[8],
                1,
                0,
            )
    leg_lines = []
    for key in leg_dict:
        leg_lines.append(leg_dict[key])
    return leg_lines


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


def make_leg_map_from_db(
    conn: Connection,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> str:
    leg_lines = get_leg_lines_from_db(conn, start_date, end_date)
    return make_leg_map([], leg_lines)


@dataclass
class StationPair:
    board_station: str = Field(alias="from")
    alight_station: str = Field(alias="to")


def make_leg_map_from_station_pair_list(
    conn: Connection,
    network: MultiDiGraph,
    station_pair_data: list[StationPair],
) -> str:
    leg_lines = []
    leg_dict = {}
    stations = set()
    for pair in station_pair_data:
        board_station = pair.board_station
        alight_station = pair.alight_station
        stations.add(board_station)
        stations.add(alight_station)
    station_lat_lons = get_station_lonlats_from_names(conn, list(stations))
    for pair in station_pair_data:
        board_station = pair.board_station
        alight_station = pair.alight_station

    for key in leg_dict:
        leg_line = leg_dict[key]
        leg_lines.append(leg_line)

    return make_leg_map([], leg_lines)


def make_leg_map_from_station_pair_file(
    network: MultiDiGraph, leg_file: str | Path
) -> str:
    with open(leg_file, "r") as f:
        leg_list = json.load(f)
    leg_list_objects = [StationPair(leg["from"], leg["to"]) for leg in leg_list]
    with connect() as (conn, _):
        return make_leg_map_from_station_pair_list(
            conn, network, leg_list_objects
        )


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


def make_leg_map_from_linestrings(
    map_points: list[MapPoint], line_strings: list[LineString]
) -> str:
    leg_lines = [
        LegLine("", "", line_string, "#000000", 0, 0)
        for (i, line_string) in enumerate(line_strings)
    ]
    return make_leg_map(map_points, leg_lines)


def get_linestring_for_leg(
    network: MultiDiGraph, conn: Connection, leg: ShortLeg
) -> tuple[MultiDiGraph, LegLine]:
    leg_calls = leg.calls
    paths = []
    points = []
    for i in range(0, len(leg_calls) - 1):
        first_call = leg_calls[i]
        second_call = leg_calls[i + 1]
        (new_network, path) = find_path_between_stations(
            network,
            conn,
            first_call.station.crs,
            first_call.platform,
            second_call.station.crs,
            second_call.platform,
        )
        paths.append(path)
        network = new_network
    complete_path = merge_linestrings(paths)
    return (
        network,
        LegLine(
            leg.calls[0].station.name,
            leg.calls[-1].station.name,
            complete_path,
            get_operator_colour_from_leg(leg),
            0,
            0,
        ),
    )


def get_linestring_for_station_pair(
    network: MultiDiGraph, conn: Connection, leg: StationPair
) -> tuple[MultiDiGraph, Optional[LegLine]]:
    first_call = leg.alight_station
    second_call = leg.board_station
    station_points = get_station_points_from_names(
        conn, [(first_call, None), (second_call, None)]
    )
    network = insert_node_dict_to_network(network, station_points)
    path = find_path_between_nodes(
        network, station_points[first_call], station_points[second_call]
    )
    if path is None:
        return (network, None)
    legline = LegLine(
        first_call,
        second_call,
        path,
        "#000000",
        0,
        0,
    )
    return (network, legline)


def get_leglines_for_legs(
    network: MultiDiGraph, conn: Connection, legs: list[ShortLeg]
) -> tuple[MultiDiGraph, list[LegLine]]:
    leg_strings = []
    for leg in legs:
        (network, legstring) = get_linestring_for_leg(network, conn, leg)
        leg_strings.append(legstring)
    return (network, leg_strings)


def get_leglines_for_station_pairs(
    network: MultiDiGraph, conn: Connection, legs: list[StationPair]
) -> tuple[MultiDiGraph, list[LegLine]]:
    leg_strings = []
    for leg in legs:
        (network, legstring) = get_linestring_for_station_pair(
            network, conn, leg
        )
        leg_strings.append(legstring)
    return (network, leg_strings)


def get_leg_map_page(
    network: MultiDiGraph,
    conn: Connection,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
    search_leg_id: Optional[int] = None,
) -> str:
    legs = select_legs(conn, search_start, search_end, search_leg_id)
    (network, leg_lines) = get_leglines_for_legs(network, conn, legs)
    html = make_leg_map([], leg_lines)
    return html


def get_leg_map_page_from_station_pair_list(
    network: MultiDiGraph, conn: Connection, legs: list[StationPair]
) -> str:
    (network, leg_lines) = get_leglines_for_station_pairs(network, conn, legs)
    html = make_leg_map([], leg_lines)
    return html


def get_leg_map_page_from_station_pair_file(
    network: MultiDiGraph, leg_file: str | Path
) -> str:
    with open(leg_file, "r") as f:
        leg_list = json.load(f)
    leg_list_objects = [StationPair(leg["from"], leg["to"]) for leg in leg_list]
    with connect() as (conn, _):
        return get_leg_map_page_from_station_pair_list(
            network, conn, leg_list_objects
        )


if __name__ == "__main__":
    network_path = sys.argv[1]
    network = ox.load_graphml(network_path)
    html = get_leg_map_page_from_station_pair_file(network, sys.argv[3])
    with open(sys.argv[2], "w+") as f:
        f.write(html)
