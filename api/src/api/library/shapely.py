import shapely
from shapely import Point


def get_distance(source: Point, target: Point) -> float:
    return shapely.distance(source, target)  # type: ignore
