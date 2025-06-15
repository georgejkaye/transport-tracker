import shapely
from shapely import Geometry, Point


def get_distance(source: Point, target: Point) -> float:
    return shapely.distance(source, target)  # type: ignore[no-untyped-call]


def get_length(geometry: Geometry) -> float:
    return shapely.length(geometry)  # type: ignore[no-untyped-call]
