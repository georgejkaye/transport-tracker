import osmnx as ox

from api.data.environment import get_env_variable

network_path = get_env_variable("NETWORK_PATH")
print(f"Loading network from {network_path}")
network = ox.load_graphml(network_path)
