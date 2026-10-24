from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlencode

from api.pull.train.classes.location import RttLocationResponse
from api.pull.train.classes.tokens import AccessToken
from api.utils.request import make_get_request


class RttApiClientInterface(ABC):
    @abstractmethod
    def get_access_token(self, refresh_token: str) -> AccessToken:
        pass


class RttApiClient(RttApiClientInterface):
    base_url = "https://data.rtt.io/api"

    def get_access_token(self, refresh_token: str) -> AccessToken:
        endpoint = f"{self.base_url}/get_access_token"
        result = make_get_request(endpoint, token=refresh_token)
        json = result.json()
        return AccessToken(
            json["token"], json["entitlements"], json["validUntil"]
        )
