import sys

from api.network.network import get_node_id_from_crs_and_platform

crs = sys.argv[1]
if len(sys.argv) == 3:
    platform = sys.argv[2]
else:
    platform = None

encoded = get_node_id_from_crs_and_platform(crs, platform)
print(encoded)
