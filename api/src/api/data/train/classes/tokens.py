from dataclasses import dataclass


@dataclass
class AccessToken:
    token: str
    entitlements: list[str]
    validUntil: str