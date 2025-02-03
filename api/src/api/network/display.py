import sys

from api.network.map import get_leg_map_from_gml_file

html = get_leg_map_from_gml_file(sys.argv[1])
with open(sys.argv[2], "w+") as f:
    f.write(html)
