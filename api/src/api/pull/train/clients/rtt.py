from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlencode

from api.pull.train.classes.location import RttLocationResponse
from api.utils.request import make_get_request


class RttRttClientInterface(ABC):
    @abstractmethod
    def get_location(
        self,
        code: str,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        filter_from: Optional[str] = None,
        filter_to: Optional[str] = None,
    ) -> RttLocationResponse:
        pass


class RttRttClient(RttRttClientInterface):
    base_url = "https://data.rtt.io/rtt"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def get_location(
        self,
        code: str,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        filter_from: Optional[str] = None,
        filter_to: Optional[str] = None,
    ) -> RttLocationResponse:
        parameters = {"code": code}
        if time_from is not None:
            parameters["timeFrom"] = time_from
        if time_to is not None:
            parameters["timeTo"] = time_to
        if filter_from is not None:
            parameters["filterFrom"] = filter_from
        if filter_to is not None:
            parameters["filterTo"] = filter_to
        query = urlencode(parameters)
        endpoint = f"{self.base_url}/rtt/location?{query}"
        result = make_get_request(endpoint, token=self.access_token)
        return RttLocationResponse.from_dict(result.json())
