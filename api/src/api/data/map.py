import json
import sys
import folium
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from psycopg import Connection
from pathlib import Path
from typing import Optional

from api.data.database import connect
from api.data.stations import get_station_latlons_from_names
from pydantic import Field


@dataclass
class LegLine:
    board_station: str
    board_lat: Decimal
    board_lon: Decimal
    alight_station: str
    alight_lat: Decimal
    alight_lon: Decimal
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
                row[1], row[2], row[3], row[5], row[6], row[7], row[8], 1, 0
            )
    leg_lines = []
    for key in leg_dict:
        leg_lines.append(leg_dict[key])
    return leg_lines


def make_leg_map(leg_lines: list[LegLine]) -> str:
    m = folium.Map(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        location=(53.906602, -1.933667),
        zoom_start=6,
    )
    for leg_line in leg_lines:
        coordinates = [
            (leg_line.board_lat, leg_line.board_lon),
            (leg_line.alight_lat, leg_line.alight_lon),
        ]
        tooltip = f"{leg_line.board_station} to {leg_line.alight_station} ({leg_line.count_lr})"
        if leg_line.count_rl > 0:
            tooltip = f"{tooltip}, {leg_line.alight_station} to {leg_line.board_station} ({leg_line.count_rl})"
        folium.PolyLine(
            coordinates,
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
    return make_leg_map(leg_lines)


@dataclass
class StationPair:
    board_station: str = Field(alias="from")
    alight_station: str = Field(alias="to")


def make_leg_map_from_station_pair_list(
    conn: Connection,
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
    station_lat_lons = get_station_latlons_from_names(conn, list(stations))
    for pair in station_pair_data:
        board_station = pair.board_station
        alight_station = pair.alight_station
        if leg_dict.get((board_station, alight_station)) is not None:
            leg_dict[(board_station, alight_station)].count_lr = (
                leg_dict[(board_station, alight_station)].count_lr + 1
            )
        elif leg_dict.get((alight_station, board_station)) is not None:
            leg_dict[(alight_station, board_station)].count_rl = (
                leg_dict[(alight_station, board_station)].count_rl + 1
            )
        else:
            (board_lat, board_lon) = station_lat_lons[board_station]
            (alight_lat, alight_lon) = station_lat_lons[alight_station]
            leg_dict[(board_station, alight_station)] = LegLine(
                board_station,
                board_lat,
                board_lon,
                alight_station,
                alight_lat,
                alight_lon,
                "#000000",
                1,
                0,
            )

    for key in leg_dict:
        leg_line = leg_dict[key]
        leg_lines.append(leg_line)

    return make_leg_map(leg_lines)


def make_leg_map_from_station_pair_file(leg_file: str | Path) -> str:
    with open(leg_file, "r") as f:
        leg_list = json.load(f)
    leg_list_objects = [StationPair(leg["from"], leg["to"]) for leg in leg_list]
    with connect() as (conn, _):
        return make_leg_map_from_station_pair_list(conn, leg_list_objects)


if __name__ == "__main__":
    html = make_leg_map_from_station_pair_file(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        f.write(html)
