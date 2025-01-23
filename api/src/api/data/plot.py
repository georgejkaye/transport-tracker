import folium
from streamlit_folium import st_folium
from api.data.network import wgs84

m = folium.Map(crs="EPSG4326")

map = st_folium(m, width=1920, height=1080)

clicked = map["last_clicked"]

if clicked is not None:
    print(f"{map["last_clicked"]["lat"]}, {map["last_clicked"]["lng"]}")
