from typing import Any, cast

import shapely
from shapely import Geometry, Point


def get_distance(source: Point, target: Point) -> float:
    return cast(float, cast(Any, shapely).distance(source, target))


def get_length(geometry: Geometry) -> float:
    return cast(float, cast(Any, shapely).length(geometry))
