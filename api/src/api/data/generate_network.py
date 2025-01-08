import sys
import osmnx as ox

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError("No output path specified")

    network = ox.graph.graph_from_place(
        ["United Kingdom"],
        custom_filter='["railway" ~ "rail"]["service" != "siding"]["service" != "yard"][service != "spur"]["passenger" != "no"]',
    )
    ox.io.save_graphml(network, sys.argv[1])
