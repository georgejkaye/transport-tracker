from api.pull.train.classes.tokens import AccessToken
from api.pull.train.clients.api import RttApiClientInterface
from api.utils.environment import get_mandatory_secret


class RttApiManager:
    rtt_refresh_token_variable_name = "RTT_REFRESH_TOKEN_SECRET_FILE"

    def __init__(self, rtt_api_client: RttApiClientInterface):
        self.rtt_api_client = rtt_api_client

    def get_access_token(self) -> AccessToken:
        refresh_token = get_mandatory_secret(
            self.rtt_refresh_token_variable_name
        )
        return self.rtt_api_client.get_access_token(refresh_token)
