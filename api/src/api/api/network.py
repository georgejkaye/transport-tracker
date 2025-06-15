from api.library.networkx import load_osmnx_graphml

from api.utils.environment import get_env_variable

network_path = get_env_variable("NETWORK_PATH")

if (network_path) is None:
    raise RuntimeError("Could not get environment variable NETWORK_PATH")

print(f"Loading network from {network_path}")
network = load_osmnx_graphml(network_path)
