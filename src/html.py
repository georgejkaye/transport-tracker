import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from dirs import templates_dir, output_html, output_log


def slug(string):
    return string.lower().replace(" ", "-")


index_template = Path(templates_dir + "index.html")

env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(),
)

env.filters["slug"] = slug

index = env.get_template("index.html")

with open(output_log) as logfile:
    journeys = yaml.safe_load(logfile)

html = index.render(journeys=journeys)


with open(output_html, "w+") as file:
    file.write(html)
