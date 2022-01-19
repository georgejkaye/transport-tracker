from pathlib import Path

templates_dir = "templates/"
output_dir = "out/"
data_dir = "data/"

stations_list = Path(data_dir + "stations.yml")
lnwr_file = Path(data_dir + "lnwr.yml")

output_log = Path(output_dir + "log.yml")
output_html = Path(output_dir + "index.html")
