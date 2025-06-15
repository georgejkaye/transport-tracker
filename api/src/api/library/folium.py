from folium import Map, PolyLine


def render_map(m: Map) -> str:
    return m.get_root().render()  # type: ignore


def create_polyline(
    locations: list[tuple[float, float]], colour: str, tooltip: str, weight: int
) -> PolyLine:
    return PolyLine(locations, color=colour, tooltip=tooltip, weight=weight)  # type: ignore[no-untyped-call]
