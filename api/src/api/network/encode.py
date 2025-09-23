import sys
from typing import Optional

from api.classes.train.legs import get_node_id_from_crs_and_platform

crs = sys.argv[1]

platform: Optional[str] = None

if len(sys.argv) == 3:
    platform = sys.argv[2]

encoded = get_node_id_from_crs_and_platform(crs, platform)
print(encoded)
