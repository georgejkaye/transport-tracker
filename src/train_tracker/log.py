import json
import sys
import sass  # type:ignore
import os
from shutil import copy
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from dirs import templates_dir, assets_dir


def slug(string):
    return string.lower().replace(" ", "-")


if __name__ == "__main__":
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

    output_dir_path = Path(output_dir)
    assets_dir_path = Path(assets_dir)

    try:
        os.mkdir(output_dir)
    except:
        pass

    scss_file = Path(assets_dir_path / "styles.scss")
    font_file = Path(assets_dir_path / "rail-alphabet.ttf")

    output_file = Path(output_dir_path / "index.html")
    output_css = Path(output_dir_path / "styles.css")

    with open(input_log) as logfile:
        data = json.load(logfile)

    html = index.render(data=data)

    with open(output_file, "w+") as file:
        file.write(html)

    with open(scss_file, "r") as file:
        scss = file.read()

    css = sass.compile(string=scss)

    with open(output_css, "w+") as file:
        file.write(css)

    scripts_file = Path(assets_dir_path / "scripts.js")
    output_scripts_file = Path(output_dir_path / "scripts.js")
    copy(scripts_file, output_scripts_file)

    output_font_file = Path(output_dir_path / "rail-alphabet.ttf")
    copy(font_file, output_font_file)

    assets_imgs_dir = Path(assets_dir_path / "imgs")
    output_imgs_dir = Path(output_dir_path / "imgs")

    try:
        os.mkdir(output_imgs_dir)
    except:
        pass

    for img in os.listdir(assets_imgs_dir):
        filename = os.fsdecode(img)
        input_file = Path(assets_imgs_dir / filename)
        output_file = Path(output_imgs_dir / filename)
        copy(input_file, output_file)
