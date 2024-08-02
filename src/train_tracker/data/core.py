from json import JSONDecodeError
import xml.etree.ElementTree as ET
import gzip
import os
import shutil
import zipfile
from bs4 import BeautifulSoup
import requests

from pathlib import Path
from typing import Any, Optional
from dotenv import dotenv_values
from requests import Response
from requests.auth import HTTPBasicAuth

from train_tracker.data.credentials import Credentials
from train_tracker.debug import debug_msg


def get_or_throw[T](t: Optional[T]) -> T:
    if t is None:
        raise RuntimeError("Expected Some but got None")
    return t


def get_or_default[T](t: Optional[T], default: T) -> T:
    if t is None:
        return default
    return t


env_values = dotenv_values()
data_dir = get_or_default(env_values.get("DATA_DIR"), "data")
data_directory = Path(data_dir)


def extract_zip(zip_path: str | Path, output_path: str | Path, delete: bool = False):
    with zipfile.ZipFile(zip_path, "r") as f:
        f.extractall(output_path)
    if delete:
        os.remove(zip_path)


def extract_gz(gz_path: str | Path, output_path: str | Path, delete: bool = False):
    with gzip.open(gz_path, "rb") as f:
        with open(output_path, "wb") as out:
            shutil.copyfileobj(f, out)
    if delete:
        os.remove(gz_path)


def download_binary(url: str, path: str, credentials: Optional[Credentials] = None):
    response = make_get_request(url, credentials=credentials, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"Could not get {url}")
    with open(path, "wb+") as f:
        f.write(response.raw.read())


def prefix_namespace(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def get_tag_text(root: ET.Element, tag: str, namespace: Optional[str] = None) -> str:
    if namespace is not None:
        tag = prefix_namespace(namespace, tag)
    content: Any = get_or_throw(root.find(tag))
    return get_or_throw(content.text)


def soupify(doc: str) -> Optional[BeautifulSoup]:
    try:
        soup = BeautifulSoup(doc, "html.parser")
    except:
        return None
    return soup


def make_get_request(
    url: str,
    credentials: Optional[Credentials] = None,
    stream: bool = False,
    headers: Optional[dict] = None,
) -> Response:
    if credentials is not None:
        auth = HTTPBasicAuth(credentials.user, credentials.password)
    else:
        auth = None
    debug_msg(f"Making request to {url}")
    return requests.get(url, auth=auth, stream=stream, headers=headers)


def get_json(
    url: str, credentials: Optional[Credentials] = None, headers: Optional[dict] = None
) -> Optional[dict]:
    response = make_get_request(url, credentials=credentials)
    try:
        json = response.json()
    except JSONDecodeError:
        return None
    return json


def get_soup(url: str) -> Optional[BeautifulSoup]:
    response = make_get_request(url)
    html = response.text
    return soupify(html)


def make_post_request(
    url: str, headers: Optional[dict] = None, data: Optional[dict] = None
) -> Response:
    print(f"Making post request to {url}")
    return requests.post(url, headers=headers, data=data)


def get_post_json(
    url: str, headers: Optional[dict] = None, data: Optional[dict] = None
) -> dict:
    response = make_post_request(url, headers, data)
    if response.status_code != 200:
        print(f"Error {response.status_code} received")
        exit(1)
    else:
        return response.json()
