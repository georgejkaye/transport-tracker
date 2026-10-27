from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from urllib.parse import urlencode

from api.pull.train.classes.gbnr.location import RttGbnrLocationResponse
from api.pull.train.classes.gbnr.service import RttGbnrServiceResponse
from api.utils.request import make_get_request


class RttGbnrClientInterface(ABC):
    @abstractmethod
    def get_location(
        self,
        code: str,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        filter_from: Optional[str] = None,
        filter_to: Optional[str] = None,
    ) -> RttGbnrLocationResponse:
        pass

    @abstractmethod
    def get_service_by_unique_identity(
        self,
        unique_identity: str,
        detailed: bool = False,
    ) -> RttGbnrServiceResponse:
        pass

    @abstractmethod
    def get_service_by_identity_and_departure_date(
        self,
        identity: str,
        departure_date: date,
        detailed: bool = False,
    ) -> RttGbnrServiceResponse:
        pass


class RttGbnrClient(RttGbnrClientInterface):
    base_url = "https://data.rtt.io/gb-nr"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def get_location(
        self,
        code: str,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        filter_from: Optional[str] = None,
        filter_to: Optional[str] = None,
    ) -> RttGbnrLocationResponse:
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
        endpoint = f"{self.base_url}/location?{query}"
        result = make_get_request(endpoint, token=self.access_token)
        return RttGbnrLocationResponse.from_dict(result.json())

    def get_service_by_unique_identity(
        self,
        unique_identity: str,
        detailed: bool = False,
    ) -> RttGbnrServiceResponse:
        return self._get_service(
            {"uniqueIdentity": unique_identity}, detailed
        )

    def get_service_by_identity_and_departure_date(
        self,
        identity: str,
        departure_date: date,
        detailed: bool = False,
    ) -> RttGbnrServiceResponse:
        return self._get_service(
            {
                "identity": identity,
                "departureDate": departure_date.isoformat(),
            },
            detailed,
        )

    def _get_service(
        self, parameters: dict[str, str], detailed: bool
    ) -> RttGbnrServiceResponse:
        if detailed:
            parameters["detailed"] = "true"
        query = urlencode(parameters)
        endpoint = f"{self.base_url}/service?{query}"
        result = make_get_request(endpoint, token=self.access_token)
        return RttGbnrServiceResponse.from_dict(result.json())
