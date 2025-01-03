import networkx as nx
import osmnx as ox

print(ox.__version__)

G = ox.graph.graph_from_place(
    "Great Britain", custom_filter='["railway" ~ "rail"]'
)

ox.io.save_graphml(G, "graph.gml")
