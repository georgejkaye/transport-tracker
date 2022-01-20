import yaml
import sys
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from dirs import templates_dir


def slug(string):
    return string.lower().replace(" ", "-")


index_template = Path(templates_dir + "index.html")

env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(),
)

env.filters["slug"] = slug

index = env.get_template("index.html")

if len(sys.argv) != 3:
    print("Usage: python " + sys.argv[0] + " <input log> <output html>")
    exit(1)

input_log = sys.argv[1]
output_html = sys.argv[2]

with open(input_log) as logfile:
    journeys = yaml.safe_load(logfile)

html = index.render(journeys=journeys)

with open(output_html, "w+") as file:
    file.write(html)
