import sys
import osmnx as ox


def generate_network(
    query: str | list[str | dict[str, str]] | dict, output_file: str
):
    network = ox.graph.graph_from_place(
        query,
        custom_filter='["railway" ~ "rail"]["service" != "siding"]["service" != "yard"][service != "spur"]["passenger" != "no"]',
    )
    ox.io.save_graphml(network, output_file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("No output path specified")
    if len(sys.argv) < 3:
        raise RuntimeError("No search query specified")

    generate_network(sys.argv[2], sys.argv[3])
