import os
import sys

from api.data.database import connect, disconnect, insert

files = os.listdir(sys.argv[1])

station_fields = ["station_crs", "station_img"]
station_values = []

(conn, cur) = connect()
statement = "UPDATE Station SET station_img = %(img)s WHERE station_crs = %(crs)s"
for file in files:
    print(file)
    if "webp" in file:
        file_name = os.path.basename(file).split(".")[0]
        crs = file_name.upper()
        url = f"{sys.argv[2]}/{file}"
        cur.execute(statement, {"img": url, "crs": crs})
conn.commit()
disconnect(conn, cur)
