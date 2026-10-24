import gzip
import os
import shutil
import zipfile
from pathlib import Path


def extract_zip(
    zip_path: str | Path, output_path: str | Path, delete: bool = False
) -> None:
    with zipfile.ZipFile(zip_path, "r") as f:
        f.extractall(output_path)
    if delete:
        os.remove(zip_path)


def extract_gz(
    gz_path: str | Path, output_path: str | Path, delete: bool = False
) -> None:
    with gzip.open(gz_path, "rb") as f:
        with open(output_path, "wb") as out:
            shutil.copyfileobj(f, out)
    if delete:
        os.remove(gz_path)
