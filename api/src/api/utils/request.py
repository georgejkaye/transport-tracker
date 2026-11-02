from typing import Any, Optional

import requests
from bs4 import BeautifulSoup
from requests import Response

from api.utils.debug import debug_msg


def _add_bearer_token_to_headers(
    headers: dict[str, str], token: Optional[str]
) -> dict[str, str]:
    if token is None:
        return headers
    return {**headers, "Authorization": f"Bearer {token}"}


def make_get_request(
    url: str,
    token: Optional[str] = None,
    stream: bool = False,
    headers: dict[str, str] = {},
) -> Response:
    debug_msg(f"Making request to {url}")
    headers = _add_bearer_token_to_headers(headers, token)
    return requests.get(url, stream=stream, headers=headers)


def make_post_request(
    url: str,
    token: Optional[str] = None,
    headers: dict[str, str] = {},
    data: Optional[dict[str, Any]] = None,
) -> Response:
    print(f"Making post request to {url}")
    headers = _add_bearer_token_to_headers(headers, token)
    return requests.post(url, headers=headers, data=data)


def get_soup(url: str) -> Optional[BeautifulSoup]:
    response = make_get_request(url)
    html = response.text
    try:
        soup = BeautifulSoup(html, "html.parser")
    except:
        return None
    return soup


def get_binary(url: str, path: str) -> None:
    response = make_get_request(url, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"Could not get {url}")
    with open(path, "wb+") as f:
        f.write(response.raw.read())
