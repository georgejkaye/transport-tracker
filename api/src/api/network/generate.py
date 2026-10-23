import sys
from typing import Any

from api.library.networkx import graph_from_place, save_osmnx_graphml


def generate_network(
    query: str | list[str | dict[str, str]] | dict[str, Any], output_file: str
) -> None:
    network = graph_from_place(
        query,
        custom_filter='["railway" ~ "rail"]["service" != "siding"]["service" != "yard"][service != "spur"]["passenger" != "no"]',
    )
    save_osmnx_graphml(network, output_file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("No output path specified")
    if len(sys.argv) < 3:
        raise RuntimeError("No search query specified")

    generate_network(sys.argv[2], sys.argv[3])
