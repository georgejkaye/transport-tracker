from dataclasses import dataclass
from decimal import Decimal
from math import floor


@dataclass
class MilesAndChains:
    miles: int
    chains: int


def miles_to_miles_and_chains(miles: Decimal) -> MilesAndChains:
    just_miles = floor(miles)
    just_chains = floor(miles * 80) % 80
    return MilesAndChains(just_miles, just_chains)


def miles_and_chains_struct_to_miles(mac: MilesAndChains) -> Decimal:
    return Decimal(mac.miles * 80 + mac.chains) / 80


def miles_and_chains_to_miles(miles: int, chains: int) -> Decimal:
    return miles_and_chains_struct_to_miles(MilesAndChains(miles, chains))
