from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import sys
from api.data.database import connect
import folium
from psycopg import Connection


@dataclass
class LegLine:
    board_station: str
    board_lat: Decimal
    board_lon: Decimal
    alight_station: str
    alight_lat: Decimal
    alight_lon: Decimal
    colour: str
    width: int


def get_leg_line(
    conn: Connection, start_date: datetime, end_date: datetime
) -> list[LegLine]:
    rows = conn.execute(
        "SELECT * FROM GetLegLines(%s, %s)", [start_date, end_date]
    ).fetchall()
    leg_dict = {}
    for row in rows:
        board_crs = row[0]
        alight_crs = row[4]
        colour = row[8]
        if leg_dict.get((board_crs, alight_crs, colour)) is not None:
            leg_dict[(board_crs, alight_crs, colour)].width = (
                leg_dict[(board_crs, alight_crs, colour)].width + 1
            )
        elif leg_dict.get((board_crs, alight_crs, colour)) is not None:
            leg_dict[(board_crs, alight_crs, colour)].width = (
                leg_dict[(board_crs, alight_crs, colour)].width + 1
            )
        else:
            leg_dict[(board_crs, alight_crs, colour)] = LegLine(
                row[1], row[2], row[3], row[5], row[6], row[7], row[8], 1
            )
    leg_lines = []
    for key in leg_dict:
        leg_lines.append(leg_dict[key])
    return leg_lines


def make_leg_map(
    conn: Connection,
    html_file: Path | str,
    start_date: datetime,
    end_date: datetime,
):
    m = folium.Map(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        location=(53.906602, -1.933667),
        zoom_start=6,
        zoom_control=False,
        control_scale=False,
    )
    leg_lines = get_leg_line(conn, start_date, end_date)
    for leg_line in leg_lines:
        print(leg_line)
        coordinates = [
            (leg_line.board_lat, leg_line.board_lon),
            (leg_line.alight_lat, leg_line.alight_lon),
        ]
        folium.PolyLine(
            coordinates,
            color=leg_line.colour,
            popup="hello!",
            tooltip=f"{leg_line.board_station} to {leg_line.alight_station}",
            weight=4,
        ).add_to(m)

    m.save(html_file)


if __name__ == "__main__":
    with connect() as (conn, _):
        make_leg_map(
            conn,
            sys.argv[1],
            datetime(int(sys.argv[2]), 1, 1),
            datetime(int(sys.argv[2]), 12, 31),
        )
