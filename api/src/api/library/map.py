from folium import Map


def render_map(m: Map) -> str:
    return m.get_root().render()  # type: ignore
