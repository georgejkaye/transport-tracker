from typing import Any, cast

from folium import Map, PolyLine


def render_map(m: Map) -> str:
    root = cast(Any, m.get_root())
    return cast(str, root.render())


def create_polyline(
    locations: list[tuple[float, float]], colour: str, tooltip: str, weight: int
) -> PolyLine:
    constructor = cast(Any, PolyLine)
    return cast(
        PolyLine,
        constructor(locations, color=colour, tooltip=tooltip, weight=weight),
    )
