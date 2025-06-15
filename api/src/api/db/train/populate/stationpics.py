import os
import sys

from api.utils.database import connect, get_db_connection_data_from_args

files = os.listdir(sys.argv[1])

station_fields = ["station_crs", "station_img"]

connection_data = get_db_connection_data_from_args()
with connect(connection_data) as conn:
    statement = (
        "UPDATE Station SET station_img = %(img)s WHERE station_crs = %(crs)s"
    )
    for file in files:
        if "webp" in file:
            file_name = os.path.basename(file).split(".")[0]
            crs = file_name.upper()
            url = f"{sys.argv[2]}/{file}"
            print(f"Inserting image for {crs}...")
            conn.execute(statement, {"img": url, "crs": crs})
    conn.commit()
