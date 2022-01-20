import yaml
import sys
import sass
import os
from shutil import copy
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from dirs import templates_dir, assets_dir


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
    print("Usage: python " + sys.argv[0] + " <input log> <output dir>")
    exit(1)

input_log = sys.argv[1]
output_dir = sys.argv[2]

try:
    os.mkdir(output_dir)
except:
    pass

scss_file = Path(assets_dir + "/styles.scss")

output_file = Path(output_dir + "/index.html")
output_css = Path(output_dir + "/styles.css")

with open(input_log) as logfile:
    journeys = yaml.safe_load(logfile)

html = index.render(journeys=journeys)

with open(output_file, "w+") as file:
    file.write(html)

with open(scss_file, "r") as file:
    scss = file.read()

css = sass.compile(string=scss)

with open(output_css, "w+") as file:
    file.write(css)

assets_imgs_dir = Path(assets_dir + "/imgs")
output_imgs_dir = Path(output_dir + "/imgs")

try:
    os.mkdir(output_imgs_dir)
except:
    pass

for file in os.listdir(assets_imgs_dir):
    filename = os.fsdecode(file)
    input_file = Path(assets_dir + "/imgs/" + filename)
    output_file = Path(output_dir + "/imgs/" + filename)
    copy(input_file, output_file)
